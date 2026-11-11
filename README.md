# mobile-robot-trajectory-control
Trajectory control for a mobile robot in CoppeliaSim.

[![Watch the video](https://img.youtube.com/vi/HflQXuMurJk/maxresdefault.jpg)](https://www.youtube.com/watch?v=HflQXuMurJk)

# Quickstart: full stack in Docker, scene in the web browser

No local CoppeliaSim install needed: CoppeliaSim runs headless in Docker and streams the scene to the browser.

```bash
# Build once (downloads CoppeliaSim 4.10.0, ~260 MB)
docker compose -f docker/docker-compose.yml --profile webvis build

# Start headless CoppeliaSim + the web UI
docker compose -f docker/docker-compose.yml --profile webvis up
```

Then open **http://localhost:8000**:
1. Choose the trajectory and set the parameters (defaults come from [parameters1.yaml](python_scripts/parameters1.yaml)).
2. Press **▶ Start**. The robot aligns with the start point (yellow dot), drives to it, then tracks the trajectory.
3. Press **■ Stop** at any time. The robot and the simulation stop, and the scene resets so you can run again.

Stop everything with `docker compose -f docker/docker-compose.yml --profile webvis down`.

| Service | URL / port | What it is |
|---|---|---|
| `webvis` | http://localhost:8000 | Parameter form, Start/Stop, trajectory preview, controller log ([backend](webvis/backend/server.py), [frontend](webvis/frontend/)) |
| `coppeliasim` | http://localhost:23020 | CoppeliaSim's Three.js "Visualization stream" (embedded in the UI) |
| `coppeliasim` | `localhost:23000` | ZeroMQ remote API used by [main.py](python_scripts/main.py) |

How it works:
- The `coppeliasim` container ([Dockerfile.coppeliasim](docker/Dockerfile.coppeliasim)) runs `coppeliaSim.sh -H` (true headless, no X server) with the scene loaded and the Visualization stream add-on auto-started. It stays idle until a client starts the simulation.
- Pressing Start makes the backend write the form values to `python_scripts/parameters_webvis.yaml` (your `parameters1.yaml` is never modified) and run `main.py parameters_webvis.yaml`, which connects to `coppeliasim:23000`.
- Pressing Stop sends SIGTERM to `main.py`, which stops the wheels and calls `sim.stopSimulation()`.
- The image adds a small fix to CoppeliaSim's Three.js viewer ([docker/coppeliasim/](docker/coppeliasim/)). Without it, the coplanar meshes of compound shapes, such as the floor tiles and their black base, z-fight and show black patches on the floor.
- Since port 23000 is published, you can also run `python3 main.py parameters1.yaml` from the host against the headless simulator.
- Choose another CoppeliaSim release with the `COPPELIASIM_VERSION` build arg in [docker-compose.yml](docker/docker-compose.yml).

# How to run with Docker (CoppeliaSim GUI on the host)

1. Download [CoppeliaSim](https://www.coppeliarobotics.com/) and run it on the host machine.
2. Open the simulation scene [pioneer_p3dx.ttt](simulation_scenes/pioneer_p3dx.ttt) from CoppeliaSim.
3. Build the Docker image (only needed once, or after changing `requirements.txt`):
```bash
docker compose -f docker/docker-compose.yml --profile host build
```
4. Run the controller:
```bash
docker compose -f docker/docker-compose.yml --profile host up
```
The container uses `network_mode: host` so it connects to CoppeliaSim's ZMQ server at `localhost:23000` without any extra configuration. The ZMQ address can be changed with the `COPPELIASIM_HOST` and `COPPELIASIM_PORT` environment variables.

To switch trajectories, edit [python_scripts/parameters1.yaml](python_scripts/parameters1.yaml) — the directory is mounted as a volume, so no rebuild is needed.

# How to run the code
1. Download [CoppeliaSim](https://www.coppeliarobotics.com/).
2. If you are on Linux, go the folder where you extracted then run it:
```bash
cd folder/where/coppeliasim/is
./coppeliaSim.sh
``` 
1. From CoppeliaSim, open the simulation scene [pioneer_p3dx.ttt](pioneer_p3dx.ttt) that is located in this repository.
2. Install the Zmq Interface for CoppeliaSim in Python (see instructions below).
3. Run the main.py script:
```bash
cd python-scripts
python3 main.py parameters1.yaml
```
1. The robot should follow a circle trajectory. Check the [parameters1.yaml](python_scripts/parameters1.yaml) to choose another trajectory.

# Installing with requirements.txt
```bash
python3 -m pip install -r requirements.txt
```

# Installing Zmq Interface for CoppeliaSim and Python
Follow the instructions on [this link](https://github.com/CoppeliaRobotics/zmqRemoteApi/tree/master/clients/python).
```bash
python3 -m pip install coppeliasim-zmqremoteapi-client
```
Simple example of using the zmq interface to start the simulation:
```bash
client = RemoteAPIClient()
    
sim = client.getObject('sim')

client.setStepping(True)

sim.startSimulation()
```

# Some references
- Fukao, T., Nakagawa, H., & Adachi, N. (2000). Adaptive tracking control of a nonholonomic mobile robot. IEEE Transactions on Robotics and Automation, 16(5), 609–615. https://doi.org/10.1109/70.880812

- Sarkar, N., Xiaoping Yun, & Kumar, V. (1994). Control of Mechanical Systems With Rolling Constraints. The International Journal of Robotics Research, 13(1), 55–69. https://doi.org/10.1177/027836499401300104

- Kokoska, S. . Fifty Famous Curves, Lots of Calculus Questions, And a Few Answers

- Siciliano, B., Sciavicco, L., Villani, L., & Oriolo, G. (2009). Robotics Modelling, Planning and Control. 