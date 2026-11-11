#   This code is distributed WITHOUT ANY WARRANTY, without the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU Lesser General Public License for more details.
#
#   The license is distributed along with this repository or you can check
#   <http://www.gnu.org/licenses/> for more details.
#
# Contributors:
# marcos-pereira (https://github.com/marcos-pereira)

"""Web backend that edits the trajectory parameters and starts/stops main.py.

The CoppeliaSim scene itself is rendered by CoppeliaSim's own Three.js
"Visualization stream" (port 23020), which the frontend embeds in an iframe.
This server only:
  - serves the frontend (webvis/frontend)
  - reads the default parameters from python_scripts/parameters1.yaml
  - writes the parameters chosen in the browser to python_scripts/parameters_webvis.yaml
  - runs python_scripts/main.py as a subprocess (Start) and sends it SIGTERM (Stop),
    which makes main.py stop the robot and the simulation over the ZMQ remote API
"""

import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

# Directory holding main.py and the parameter files (overridable for Docker)
scripts_dir = Path(os.environ.get("SCRIPTS_DIR", Path(__file__).resolve().parents[2] / "python_scripts")).resolve()
# Directory holding the frontend (kept in its own folder, separate from the backend)
frontend_dir = Path(os.environ.get("FRONTEND_DIR", Path(__file__).resolve().parents[1] / "frontend")).resolve()

default_parameters_file = scripts_dir / os.environ.get("DEFAULT_PARAMETERS_FILE", "parameters1.yaml")
webvis_parameters_file = scripts_dir / "parameters_webvis.yaml"

# Port of CoppeliaSim's Three.js viewer, as reachable from the browser
viewer_port = int(os.environ.get("VIEWER_PORT", "23020"))

# Trajectory types implemented in main.py
trajectory_types = ["circle", "lemniscate", "epicycloid", "hypocycloid"]

# Parameters that must be strictly positive
positive_parameters = {
    "sampling_time", "circle_radius", "circle_period", "desired_alignment_error",
    "desired_euclidean_error", "control_gain", "half_lemniscate_size", "lemniscate_period",
    "epicycloid_period", "hypocycloid_period", "epicycloid_b", "hypocycloid_b",
}

# Upper bound on trajectory samples, so a typo can't make main.py allocate forever
max_trajectory_samples = 2_000_000

# Matches the progress line printed by main.py during tracking
step_pattern = re.compile(r"Trajectory step: (\d+), total: (\d+)")

@asynccontextmanager
async def stop_controller_on_shutdown(application: FastAPI):
    """Don't leave main.py stepping the simulation after the server exits."""
    yield
    if controller_run.is_running():
        stop_controller()


app = FastAPI(title="Mobile Robot Trajectory Control Web Visualizer", lifespan=stop_controller_on_shutdown)


class ControllerRun:
    """The main.py subprocess and what it has printed so far."""

    def __init__(self):
        self.lock = threading.Lock()
        self.process: subprocess.Popen | None = None
        self.log_lines: deque[str] = deque(maxlen=300)
        self.phase = "idle"
        self.step = 0
        self.total_steps = 0
        self.exit_code: int | None = None
        self.started_at: float | None = None
        self.parameters: dict[str, Any] = {}

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None


controller_run = ControllerRun()


def read_parameters_file(path: Path) -> dict[str, Any]:
    """Return {name: value} from a parameter YAML file in the {name: {value: ...}} format."""
    with open(path) as yaml_file:
        parameters_yaml = yaml.safe_load(yaml_file)
    return {name: entry["value"] for name, entry in parameters_yaml.items()}


def validate_parameters(submitted: dict[str, Any]) -> dict[str, Any]:
    """Check the submitted parameters against the defaults file: same names, same
    types, sensible ranges. Return the validated (type-converted) parameters."""
    defaults = read_parameters_file(default_parameters_file)

    unknown_names = set(submitted) - set(defaults)
    if unknown_names:
        raise HTTPException(400, f"Unknown parameters: {', '.join(sorted(unknown_names))}.")

    validated = dict(defaults)
    for name, value in submitted.items():
        default_value = defaults[name]
        if isinstance(default_value, str):
            validated[name] = str(value)
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise HTTPException(400, f"Parameter '{name}' must be a number.")
        if number != number or number in (float("inf"), float("-inf")):
            raise HTTPException(400, f"Parameter '{name}' must be a finite number.")
        validated[name] = number

    if validated["trajectory_type"] not in trajectory_types:
        raise HTTPException(400, f"trajectory_type must be one of: {', '.join(trajectory_types)}.")
    for name in positive_parameters & set(validated):
        if validated[name] <= 0:
            raise HTTPException(400, f"Parameter '{name}' must be greater than zero.")
    if validated["last_value"] <= validated["init_value"]:
        raise HTTPException(400, "last_value must be greater than init_value.")
    trajectory_samples = (validated["last_value"] - validated["init_value"]) / validated["sampling_time"]
    if trajectory_samples > max_trajectory_samples:
        raise HTTPException(
            400,
            f"The trajectory would have {int(trajectory_samples)} samples (max {max_trajectory_samples}). "
            "Increase sampling_time or shorten the time interval.",
        )
    return validated


def write_parameters_file(parameters: dict[str, Any], path: Path) -> None:
    """Write {name: value} in the {name: {value: ...}} format main.py expects."""
    header = (
        "# Generated by the web visualizer (webvis/backend/server.py) from the browser form.\n"
        "# Edit parameters1.yaml to change the defaults shown in the browser.\n\n"
    )
    with open(path, "w") as yaml_file:
        yaml_file.write(header)
        yaml.safe_dump({name: {"value": value} for name, value in parameters.items()}, yaml_file, sort_keys=False)


def record_output_line(line: str) -> None:
    """Update the progress/phase from a main.py output line and keep the line in
    the log, except the per-step lines that would flood it."""
    step_match = step_pattern.search(line)
    if step_match:
        controller_run.phase = "tracking"
        controller_run.step = int(step_match.group(1)) + 1
        controller_run.total_steps = int(step_match.group(2))
        return
    if line.startswith("Eucliden distance") or re.fullmatch(r"-?[\d.e+-]+", line):
        controller_run.phase = "approaching start"
        return
    if "Simulation started" in line:
        controller_run.phase = "aligning"
    controller_run.log_lines.append(line)


def pump_output(process: subprocess.Popen) -> None:
    """Read main.py output until it exits (runs in a background thread)."""
    for raw_line in process.stdout:
        line = raw_line.rstrip()
        if line:
            with controller_run.lock:
                record_output_line(line)
    exit_code = process.wait()
    with controller_run.lock:
        controller_run.exit_code = exit_code
        if controller_run.phase == "stopping":
            controller_run.phase = "stopped"
        else:
            controller_run.phase = "finished" if exit_code == 0 else "failed"
        controller_run.log_lines.append(f"🏁 main.py exited with code {exit_code}.")


def stop_simulation_directly() -> None:
    """Last resort when main.py had to be killed: stop the simulation ourselves."""
    try:
        from coppeliasim_zmqremoteapi_client import RemoteAPIClient

        client = RemoteAPIClient(
            host=os.environ.get("COPPELIASIM_HOST", "localhost"),
            port=int(os.environ.get("COPPELIASIM_PORT", "23000")),
        )
        client.require("sim").stopSimulation()
    except Exception as error:
        controller_run.log_lines.append(f"⚠️ Could not stop the simulation directly: {error}")


@app.middleware("http")
async def no_cache_static_assets(request, call_next):
    """Force browsers to revalidate the frontend files instead of using a stale copy."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/api/config")
def get_config():
    """Return what the frontend needs to embed the CoppeliaSim viewer."""
    return {"viewer_port": viewer_port, "trajectory_types": trajectory_types}


@app.get("/api/parameters")
def get_parameters(source: str = "default"):
    """Return the parameters from parameters1.yaml (source=default), or the ones
    of the last browser run when it exists (source=last)."""
    path = default_parameters_file
    if source == "last" and webvis_parameters_file.is_file():
        path = webvis_parameters_file
    return read_parameters_file(path)


@app.post("/api/start")
def start_controller(parameters: dict[str, Any]):
    """Write the parameters and start main.py, which starts the simulation."""
    validated = validate_parameters(parameters)
    with controller_run.lock:
        if controller_run.is_running():
            raise HTTPException(409, "The controller is already running. Stop it first.")
        write_parameters_file(validated, webvis_parameters_file)
        controller_run.log_lines.clear()
        controller_run.log_lines.append(f"🚀 Starting main.py with the {validated['trajectory_type']} trajectory...")
        controller_run.phase = "connecting"
        controller_run.step = 0
        controller_run.total_steps = 0
        controller_run.exit_code = None
        controller_run.started_at = time.time()
        controller_run.parameters = validated
        controller_run.process = subprocess.Popen(
            [sys.executable, "-u", "main.py", webvis_parameters_file.name],
            cwd=scripts_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        process = controller_run.process
    threading.Thread(target=pump_output, args=(process,), daemon=True).start()
    return {"started": True}


@app.post("/api/stop")
def stop_controller():
    """Ask main.py to stop (SIGTERM), so it stops the robot and the simulation.
    Kill it and stop the simulation directly if it does not exit in time."""
    with controller_run.lock:
        process = controller_run.process
        if process is None or process.poll() is not None:
            return {"stopped": False, "detail": "The controller is not running."}
        controller_run.phase = "stopping"
        controller_run.log_lines.append("🛑 Stop requested from the browser...")
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        stop_simulation_directly()
    return {"stopped": True}


@app.get("/api/status")
def get_status():
    """Return the controller state, progress and recent log lines."""
    with controller_run.lock:
        return {
            "running": controller_run.is_running(),
            "phase": controller_run.phase,
            "step": controller_run.step,
            "total_steps": controller_run.total_steps,
            "exit_code": controller_run.exit_code,
            "elapsed": (time.time() - controller_run.started_at) if controller_run.started_at else 0.0,
            "parameters": controller_run.parameters,
            "log": list(controller_run.log_lines),
        }


# Serve the frontend (mounted last so the /api routes take precedence)
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
