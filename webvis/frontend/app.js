//   This code is distributed WITHOUT ANY WARRANTY, without the implied
//   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
//   See the GNU Lesser General Public License for more details.
//
//   The license is distributed along with this repository or you can check
//   <http://www.gnu.org/licenses/> for more details.
//
// Contributors:
// marcos-pereira (https://github.com/marcos-pereira)

// ── Parameter definitions ──────────────────────────────────────────────────
// One entry per parameter of python_scripts/parameters1.yaml. "trajectory" ties a
// group to a trajectory_type, so only the active trajectory's parameters are shown.
// Parameters found in the YAML but missing here still appear, in the "Other" group.
const parameterGroups = [
    {
        title: 'Trajectory',
        fields: [
            { name: 'trajectory_type', label: 'Type', kind: 'select', wide: true },
            { name: 'init_value', label: 'Start time', unit: 's', step: 1 },
            { name: 'last_value', label: 'End time', unit: 's', step: 1 },
            { name: 'sampling_time', label: 'Sampling time', unit: 's', step: 0.001, wide: true },
        ],
    },
    {
        title: 'Controller',
        fields: [
            { name: 'control_gain', label: 'Control gain k', step: 0.1, wide: true },
            { name: 'desired_alignment_error', label: 'Alignment error', unit: 'rad', step: 0.005 },
            { name: 'desired_euclidean_error', label: 'Position error', unit: 'm', step: 0.01 },
        ],
    },
    {
        title: 'Circle', trajectory: 'circle',
        fields: [
            { name: 'circle_radius', label: 'Radius', unit: 'm', step: 0.1 },
            { name: 'circle_period', label: 'Period', unit: 's', step: 1 },
        ],
    },
    {
        title: 'Lemniscate', trajectory: 'lemniscate',
        fields: [
            { name: 'half_lemniscate_size', label: 'Half size a', unit: 'm', step: 0.1 },
            { name: 'lemniscate_period', label: 'Period', unit: 's', step: 1 },
        ],
    },
    {
        title: 'Epicycloid', trajectory: 'epicycloid',
        fields: [
            { name: 'epicycloid_a', label: 'a', unit: 'm', step: 0.1 },
            { name: 'epicycloid_b', label: 'b', unit: 'm', step: 0.1 },
            { name: 'epicycloid_period', label: 'Period', unit: 's', step: 1, wide: true },
        ],
    },
    {
        title: 'Hypocycloid', trajectory: 'hypocycloid',
        fields: [
            { name: 'hypocycloid_a', label: 'a', unit: 'm', step: 0.1 },
            { name: 'hypocycloid_b', label: 'b', unit: 'm', step: 0.1 },
            { name: 'hypocycloid_period', label: 'Period', unit: 's', step: 1, wide: true },
        ],
    },
];

// ── State ──────────────────────────────────────────────────────────────────
let trajectoryTypes = ['circle', 'lemniscate', 'epicycloid', 'hypocycloid'];
let viewerUrl = '';
let viewerOnline = null;      // null until the first probe
let isRunning = false;
let lastLogText = '';
let lastStatus = null;
let previewApp = null;        // PIXI.Application of the trajectory preview
let previewCurve = null;      // PIXI.Graphics: axes + reference curve
let previewMarker = null;     // PIXI.Graphics: current reference point while tracking
let previewTransform = null;  // maps world (x, y) [m] to preview pixels

// ── DOM refs ───────────────────────────────────────────────────────────────
const groupsEl        = document.getElementById('parameter-groups');
const startBtn        = document.getElementById('start-btn');
const stopBtn         = document.getElementById('stop-btn');
const defaultsBtn     = document.getElementById('defaults-btn');
const statusDot       = document.getElementById('status-dot');
const statusText      = document.getElementById('status-text');
const statusElapsed   = document.getElementById('status-elapsed');
const statusDetail    = document.getElementById('status-detail');
const progressBar     = document.getElementById('progress-bar');
const viewerFrame     = document.getElementById('viewer-frame');
const viewerOffline   = document.getElementById('viewer-offline');
const viewerUrlEl     = document.getElementById('viewer-url');
const openViewerLink  = document.getElementById('open-viewer-link');
const reloadViewerBtn = document.getElementById('reload-viewer-btn');
const previewEl       = document.getElementById('preview-canvas');
const previewInfo     = document.getElementById('preview-info');
const logEl           = document.getElementById('log');

// ── Helpers ────────────────────────────────────────────────────────────────
async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || `${response.status} ${response.statusText}`);
    return body;
}

function formatSeconds(seconds) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
}

// ── Form ───────────────────────────────────────────────────────────────────
function buildForm(parameters) {
    groupsEl.innerHTML = '';
    const knownNames = new Set(parameterGroups.flatMap(group => group.fields.map(field => field.name)));
    const otherFields = Object.keys(parameters)
        .filter(name => !knownNames.has(name))
        .map(name => ({ name, label: name, step: 'any', wide: true }));
    const groups = otherFields.length ? [...parameterGroups, { title: 'Other', fields: otherFields }] : parameterGroups;

    for (const group of groups) {
        const groupEl = document.createElement('div');
        groupEl.className = 'group';
        if (group.trajectory) groupEl.dataset.trajectory = group.trajectory;
        groupEl.innerHTML = `<div class="group-title">${group.title}</div><div class="fields"></div>`;
        const fieldsEl = groupEl.querySelector('.fields');

        for (const field of group.fields) {
            if (!(field.name in parameters)) continue;
            const fieldEl = document.createElement('div');
            fieldEl.className = 'field' + (field.wide ? ' wide' : '');
            const unit = field.unit ? ` <span class="unit">[${field.unit}]</span>` : '';
            fieldEl.innerHTML = `<label for="param-${field.name}" title="${field.name}">${field.label}${unit}</label>`;

            let input;
            if (field.kind === 'select') {
                input = document.createElement('select');
                for (const type of trajectoryTypes) {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    input.appendChild(option);
                }
            } else {
                input = document.createElement('input');
                input.type = 'number';
                input.step = field.step ?? 'any';
            }
            input.id = `param-${field.name}`;
            input.name = field.name;
            input.value = parameters[field.name];
            input.addEventListener('input', onParametersChanged);
            fieldEl.appendChild(input);
            fieldsEl.appendChild(fieldEl);
        }
        groupsEl.appendChild(groupEl);
    }
    updateVisibleGroups();
    drawPreview();
}

function readForm() {
    const parameters = {};
    for (const input of groupsEl.querySelectorAll('input, select')) {
        parameters[input.name] = input.type === 'number' ? Number(input.value) : input.value;
    }
    return parameters;
}

function updateVisibleGroups() {
    const trajectoryType = document.getElementById('param-trajectory_type')?.value;
    for (const groupEl of groupsEl.querySelectorAll('.group[data-trajectory]')) {
        groupEl.hidden = groupEl.dataset.trajectory !== trajectoryType;
    }
}

function onParametersChanged(event) {
    if (event.target.type === 'number') {
        event.target.classList.toggle('invalid', event.target.value === '' || !isFinite(event.target.value));
    }
    updateVisibleGroups();
    drawPreview();
}

function setFormEnabled(enabled) {
    for (const input of groupsEl.querySelectorAll('input, select')) input.disabled = !enabled;
    defaultsBtn.disabled = !enabled;
}

async function loadParameters(source) {
    try {
        buildForm(await requestJson(`/api/parameters?source=${source}`));
    } catch (error) {
        statusDetail.textContent = `⚠️ Could not load parameters: ${error.message}`;
    }
}

// ── Reference trajectory (same parametric equations as python_scripts/main.py) ─
function trajectoryPoint(parameters, t) {
    const p = parameters;
    switch (p.trajectory_type) {
        case 'circle': {
            const omega = 2 * Math.PI / p.circle_period;
            return [p.circle_radius * Math.cos(omega * t), p.circle_radius * Math.sin(omega * t)];
        }
        case 'lemniscate': {
            const omega = 2 * Math.PI / p.lemniscate_period;
            const s = Math.sin(omega * t), c = Math.cos(omega * t);
            const a = p.half_lemniscate_size;
            return [a * c / (1 + s * s), a * s * c / (1 + s * s)];
        }
        case 'epicycloid': {
            const omega = 2 * Math.PI / p.epicycloid_period;
            const a = p.epicycloid_a, b = p.epicycloid_b;
            return [
                (a + b) * Math.cos(omega * t) - b * Math.cos((a / b + 1) * omega * t),
                (a + b) * Math.sin(omega * t) - b * Math.sin((a / b + 1) * omega * t),
            ];
        }
        case 'hypocycloid': {
            const omega = 2 * Math.PI / p.hypocycloid_period;
            const a = p.hypocycloid_a, b = p.hypocycloid_b;
            return [
                (a - b) * Math.cos(omega * t) + b * Math.cos((a / b - 1) * omega * t),
                (a - b) * Math.sin(omega * t) - b * Math.sin((a / b - 1) * omega * t),
            ];
        }
        default:
            return [NaN, NaN];
    }
}

function sampleTrajectory(parameters) {
    const t0 = parameters.init_value, t1 = parameters.last_value;
    if (!(t1 > t0)) return [];
    // The preview doesn't need every controller sample; ~3000 points draw a smooth curve
    const sampleCount = 3000;
    const points = [];
    for (let i = 0; i <= sampleCount; i++) {
        const point = trajectoryPoint(parameters, t0 + (t1 - t0) * i / sampleCount);
        if (point.every(Number.isFinite)) points.push(point);
    }
    return points;
}

// ── PixiJS preview ─────────────────────────────────────────────────────────
function initPreview() {
    previewApp = new PIXI.Application({
        resizeTo: previewEl,
        backgroundAlpha: 0,
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
    });
    previewEl.appendChild(previewApp.view);
    previewCurve = new PIXI.Graphics();
    previewMarker = new PIXI.Graphics();
    previewApp.stage.addChild(previewCurve, previewMarker);
    new ResizeObserver(() => requestAnimationFrame(drawPreview)).observe(previewEl);
}

function drawPreview() {
    if (!previewApp) return;
    const parameters = readForm();
    const points = sampleTrajectory(parameters);
    const width = previewEl.clientWidth, height = previewEl.clientHeight;
    previewCurve.clear();
    previewMarker.clear();
    previewTransform = null;
    if (!points.length || width === 0 || height === 0) {
        previewInfo.textContent = 'invalid parameters';
        return;
    }

    // Fit the curve bounds (and the origin) in the panel, keeping the aspect ratio
    const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
    const xMin = Math.min(0, ...xs), xMax = Math.max(0, ...xs);
    const yMin = Math.min(0, ...ys), yMax = Math.max(0, ...ys);
    const margin = 18;
    const scale = Math.min((width - 2 * margin) / Math.max(xMax - xMin, 1e-6),
                           (height - 2 * margin) / Math.max(yMax - yMin, 1e-6));
    const offsetX = width / 2 - scale * (xMin + xMax) / 2;
    const offsetY = height / 2 + scale * (yMin + yMax) / 2;
    previewTransform = ([x, y]) => [offsetX + scale * x, offsetY - scale * y];

    // 1 m grid and the world axes
    previewCurve.lineStyle(1, 0x21262d, 1);
    for (let gx = Math.ceil(xMin); gx <= Math.floor(xMax); gx++) {
        const [px] = previewTransform([gx, 0]);
        previewCurve.moveTo(px, 0).lineTo(px, height);
    }
    for (let gy = Math.ceil(yMin); gy <= Math.floor(yMax); gy++) {
        const [, py] = previewTransform([0, gy]);
        previewCurve.moveTo(0, py).lineTo(width, py);
    }
    const [originX, originY] = previewTransform([0, 0]);
    previewCurve.lineStyle(1.5, 0xda3633, 0.9).moveTo(originX, originY).lineTo(originX + 24, originY);
    previewCurve.lineStyle(1.5, 0x3fb950, 0.9).moveTo(originX, originY).lineTo(originX, originY - 24);

    // Reference curve
    previewCurve.lineStyle(2, 0x58a6ff, 1);
    const [startX, startY] = previewTransform(points[0]);
    previewCurve.moveTo(startX, startY);
    for (let i = 1; i < points.length; i++) previewCurve.lineTo(...previewTransform(points[i]));

    // Start point (where the robot drives to before tracking)
    previewCurve.lineStyle(0).beginFill(0xffcf58).drawCircle(startX, startY, 5).endFill();

    const durationSeconds = parameters.last_value - parameters.init_value;
    const stepCount = Math.ceil(durationSeconds / parameters.sampling_time);
    previewInfo.textContent = `${durationSeconds.toFixed(0)} s · ${stepCount.toLocaleString()} steps · grid 1 m`;
    drawPreviewMarker();
}

function drawPreviewMarker() {
    previewMarker.clear();
    if (!previewTransform || !lastStatus || lastStatus.phase !== 'tracking' || !lastStatus.total_steps) return;
    // Place the marker on the curve of the parameters that are actually running
    const parameters = lastStatus.parameters;
    const t = parameters.init_value + (lastStatus.step - 1) * parameters.sampling_time;
    const point = trajectoryPoint(parameters, t);
    if (!point.every(Number.isFinite)) return;
    const [px, py] = previewTransform(point);
    previewMarker.lineStyle(2, 0x0d1117).beginFill(0x3fb950).drawCircle(px, py, 6).endFill();
}

// ── CoppeliaSim viewer (Three.js visualization stream served by CoppeliaSim) ─
async function probeViewer() {
    let online;
    try {
        // no-cors: we only need to know whether CoppeliaSim answers at all
        await fetch(viewerUrl, { mode: 'no-cors', cache: 'no-store' });
        online = true;
    } catch {
        online = false;
    }
    if (online !== viewerOnline) {
        viewerOnline = online;
        viewerOffline.hidden = online;
        if (online) viewerFrame.src = viewerUrl;
    }
    setTimeout(probeViewer, online ? 10000 : 3000);
}

function reloadViewer() {
    viewerFrame.src = 'about:blank';
    setTimeout(() => { viewerFrame.src = viewerUrl; }, 50);
}

// ── Controller start / stop / status ───────────────────────────────────────
async function startController() {
    startBtn.disabled = true;
    try {
        await requestJson('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(readForm()),
        });
        await pollStatus();
    } catch (error) {
        statusDetail.textContent = `⚠️ ${error.message}`;
        startBtn.disabled = false;
    }
}

async function stopController() {
    stopBtn.disabled = true;
    statusText.textContent = 'Stopping…';
    try {
        await requestJson('/api/stop', { method: 'POST' });
    } catch (error) {
        statusDetail.textContent = `⚠️ ${error.message}`;
    }
    await pollStatus();
}

const phaseLabels = {
    idle: 'Idle',
    connecting: 'Connecting to CoppeliaSim',
    aligning: 'Aligning with the start point',
    'approaching start': 'Driving to the start point',
    tracking: 'Tracking the trajectory',
    stopping: 'Stopping',
    stopped: 'Stopped',
    finished: 'Finished',
    failed: 'Failed',
};

function renderStatus(status) {
    lastStatus = status;
    isRunning = status.running;
    startBtn.disabled = isRunning;
    stopBtn.disabled = !isRunning;
    setFormEnabled(!isRunning);

    statusText.textContent = phaseLabels[status.phase] || status.phase;
    statusDot.className = 'dot ' + (
        status.phase === 'failed' ? 'failed'
        : status.phase === 'tracking' ? 'running'
        : isRunning ? 'busy' : 'idle');
    statusElapsed.textContent = status.elapsed && (isRunning || status.phase !== 'idle')
        ? formatSeconds(status.elapsed) : '';

    const progress = status.total_steps ? status.step / status.total_steps : 0;
    progressBar.style.width = `${(progress * 100).toFixed(1)}%`;
    if (status.phase === 'tracking') {
        statusDetail.textContent = `Step ${status.step.toLocaleString()} / ${status.total_steps.toLocaleString()} (${(progress * 100).toFixed(1)}%)`;
    } else if (status.phase === 'failed') {
        statusDetail.textContent = `main.py exited with code ${status.exit_code}. See the log.`;
    } else if (status.phase === 'idle') {
        statusDetail.textContent = 'Set the parameters and press Start.';
    } else if (!isRunning) {
        statusDetail.textContent = 'The simulation is stopped. Press Start to run again.';
    } else {
        statusDetail.textContent = 'The trajectory starts once the robot reaches the yellow point.';
    }

    const logText = status.log.join('\n');
    if (logText !== lastLogText) {
        const atBottom = logEl.scrollTop + logEl.clientHeight >= logEl.scrollHeight - 8;
        logEl.textContent = logText;
        lastLogText = logText;
        if (atBottom) logEl.scrollTop = logEl.scrollHeight;
    }
    drawPreviewMarker();
}

async function pollStatus() {
    try {
        renderStatus(await requestJson('/api/status'));
    } catch {
        statusText.textContent = 'Backend unreachable';
        statusDot.className = 'dot failed';
    }
}

function schedulePolling() {
    pollStatus().finally(() => setTimeout(schedulePolling, isRunning ? 500 : 2000));
}

// ── Startup ────────────────────────────────────────────────────────────────
async function init() {
    try {
        const config = await requestJson('/api/config');
        trajectoryTypes = config.trajectory_types;
        viewerUrl = `${location.protocol}//${location.hostname}:${config.viewer_port}/`;
    } catch {
        viewerUrl = `${location.protocol}//${location.hostname}:23020/`;
    }
    viewerUrlEl.textContent = viewerUrl;
    openViewerLink.href = viewerUrl;

    initPreview();
    // Restore the parameters of the last browser run, falling back to parameters1.yaml
    await loadParameters('last');
    probeViewer();
    schedulePolling();
}

startBtn.addEventListener('click', startController);
stopBtn.addEventListener('click', stopController);
defaultsBtn.addEventListener('click', () => loadParameters('default'));
reloadViewerBtn.addEventListener('click', reloadViewer);

init();
