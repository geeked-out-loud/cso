// CSO Visual Simulator - Main JavaScript

// ==============================================
// CANVAS RENDERING SETUP
// ==============================================

// Canvas setup
const canvas = document.getElementById('viz-canvas');
const ctx = canvas ? canvas.getContext('2d') : null;

// Constants for rendering
const WORLD_MIN = -5.12;
const WORLD_MAX = 5.12;
const CANVAS_SIZE = 800;

// Cached contour background
let contourCache = null;

/**
 * Convert world coordinates to canvas pixels
 */
function worldToCanvas(worldX, worldY) {
    const px = ((worldX - WORLD_MIN) / (WORLD_MAX - WORLD_MIN)) * CANVAS_SIZE;
    const py = ((WORLD_MAX - worldY) / (WORLD_MAX - WORLD_MIN)) * CANVAS_SIZE; // Flip Y axis
    return [px, py];
}

/**
 * Rastrigin function for contour background
 */
function rastrigin(x, y) {
    return 20 + (x * x - 10 * Math.cos(2 * Math.PI * x)) + (y * y - 10 * Math.cos(2 * Math.PI * y));
}

/**
 * Map fitness value to color gradient (blue=low/good, red=high/bad)
 */
function fitnessToColor(value) {
    const normalized = Math.min(value / 100, 1);
    const r = Math.floor(normalized * 255);
    const g = 100;
    const b = Math.floor((1 - normalized) * 200);
    return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Generate and cache contour background
 */
function generateContourBackground() {
    if (contourCache) return contourCache;
    
    console.log('[Canvas] Generating contour background...');
    
    // Create offscreen canvas for caching
    const offCanvas = document.createElement('canvas');
    offCanvas.width = CANVAS_SIZE;
    offCanvas.height = CANVAS_SIZE;
    const offCtx = offCanvas.getContext('2d');
    
    // Resolution (lower = faster, higher = smoother)
    const resolution = 100;
    const cellSize = CANVAS_SIZE / resolution;
    
    // Generate heatmap
    for (let i = 0; i < resolution; i++) {
        for (let j = 0; j < resolution; j++) {
            // Convert to world coordinates
            const x = WORLD_MIN + (i / resolution) * (WORLD_MAX - WORLD_MIN);
            const y = WORLD_MAX - (j / resolution) * (WORLD_MAX - WORLD_MIN);
            
            // Calculate Rastrigin value
            const z = rastrigin(x, y);
            
            // Map to color
            const color = fitnessToColor(z);
            
            // Draw cell
            offCtx.fillStyle = color;
            offCtx.fillRect(i * cellSize, j * cellSize, cellSize, cellSize);
        }
    }
    
    // Add grid lines
    offCtx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
    offCtx.lineWidth = 0.5;
    for (let i = 0; i <= 10; i++) {
        const pos = (i / 10) * CANVAS_SIZE;
        // Vertical line
        offCtx.beginPath();
        offCtx.moveTo(pos, 0);
        offCtx.lineTo(pos, CANVAS_SIZE);
        offCtx.stroke();
        // Horizontal line
        offCtx.beginPath();
        offCtx.moveTo(0, pos);
        offCtx.lineTo(CANVAS_SIZE, pos);
        offCtx.stroke();
    }
    
    contourCache = offCanvas;
    console.log('[Canvas] Contour background cached');
    return offCanvas;
}

/**
 * Draw a star shape
 */
function drawStar(ctx, x, y, radius, color) {
    ctx.fillStyle = color;
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
        const angle = (i * 4 * Math.PI) / 5 - Math.PI / 2;
        const r = i % 2 === 0 ? radius : radius / 2;
        const px = x + Math.cos(angle) * r;
        const py = y + Math.sin(angle) * r;
        if (i === 0) {
            ctx.moveTo(px, py);
        } else {
            ctx.lineTo(px, py);
        }
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
}

/**
 * Draw a single frame on canvas
 */
function drawFrame(frameData) {
    if (!ctx) {
        console.error('[Canvas] Canvas context not available');
        return;
    }
    
    console.log('[Canvas] Drawing frame:', frameData.iteration);
    console.log('[Canvas] Positions:', frameData.positions.length);
    console.log('[Canvas] Modes:', frameData.modes);
    
    // Clear canvas
    ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    
    // Draw contour background
    const contour = generateContourBackground();
    ctx.drawImage(contour, 0, 0);
    
    // Draw each cat
    frameData.positions.forEach((pos, i) => {
        const [px, py] = worldToCanvas(pos[0], pos[1]);
        const mode = frameData.modes[i];
        
        if (mode === 'seeking') {
            // Blue circle for seeking mode
            ctx.fillStyle = '#3B82F6';
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(px, py, 8, 0, 2 * Math.PI);
            ctx.fill();
            ctx.stroke();
        } else {
            // Red triangle for tracing mode
            ctx.fillStyle = '#EF4444';
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(px, py - 10);
            ctx.lineTo(px - 8, py + 8);
            ctx.lineTo(px + 8, py + 8);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
        }
    });
    
    // Draw global best position (gold star)
    const [bx, by] = worldToCanvas(
        frameData.global_best_position[0],
        frameData.global_best_position[1]
    );
    drawStar(ctx, bx, by, 15, '#FFD700');
    
    // Draw true optimum (green X)
    const [ox, oy] = worldToCanvas(0, 0);
    ctx.strokeStyle = '#00FF00';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(ox - 10, oy - 10);
    ctx.lineTo(ox + 10, oy + 10);
    ctx.moveTo(ox + 10, oy - 10);
    ctx.lineTo(ox - 10, oy + 10);
    ctx.stroke();
    
    // Draw iteration info with background
    const text = `Iteration ${frameData.iteration} | Fitness: ${frameData.global_best_fitness.toFixed(6)}`;
    ctx.font = 'bold 18px Inter, system-ui, sans-serif';
    
    // Background for text
    const textMetrics = ctx.measureText(text);
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(10, 10, textMetrics.width + 20, 30);
    
    // Text
    ctx.fillStyle = '#fff';
    ctx.fillText(text, 20, 30);
}

// ==============================================
// STATE MANAGEMENT
// ==============================================

// State management
let simulationState = {
    isRunning: false,
    currentFrame: 0,
    totalFrames: 0,
    isPlaying: false,
    playInterval: null,
    sessionId: null,
    wasRecovered: false,
    eventSource: null  // SSE connection
};

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');
const prevFrameBtn = document.getElementById('prev-frame');
const playPauseBtn = document.getElementById('play-pause');
const nextFrameBtn = document.getElementById('next-frame');
const statusText = document.getElementById('status-text');
const statusIndicator = document.getElementById('status-indicator');
const progressFill = document.getElementById('progress-fill');
const frameCounter = document.getElementById('frame-counter');
const vizPlaceholder = document.getElementById('viz-placeholder');
const loadingSpinner = document.getElementById('loading-spinner');
const resultsPanel = document.getElementById('results-panel');
const convergenceSection = document.getElementById('convergence-section');
const convergenceContainer = document.getElementById('convergence-container');

// Parameter inputs
const params = {
    n_cats: document.getElementById('n_cats'),
    max_iter: document.getElementById('max_iter'),
    MR: document.getElementById('MR'),
    SMP: document.getElementById('SMP'),
    SRD: document.getElementById('SRD'),
    CDC: document.getElementById('CDC'),
    c1: document.getElementById('c1'),
    w: document.getElementById('w')
};

// Event Listeners
startBtn.addEventListener('click', startSimulation);
stopBtn.addEventListener('click', stopSimulation);
resetBtn.addEventListener('click', resetSimulation);
prevFrameBtn.addEventListener('click', () => changeFrame(-1));
playPauseBtn.addEventListener('click', togglePlayPause);
nextFrameBtn.addEventListener('click', () => changeFrame(1));

// Check for existing session on page load
window.addEventListener('load', checkExistingSession);

// Start simulation
// Check for existing session (recovery after refresh)
async function checkExistingSession() {
    try {
        const response = await fetch('/api/simulation_status');
        const status = await response.json();
        
        simulationState.sessionId = status.session_id;
        
        // Check if there's an active or completed simulation
        if (status.is_running) {
            // Simulation is still running - recover it
            statusText.textContent = 'Recovering running simulation...';
            statusIndicator.className = 'status-dot running';
            
            if (status.recovered) {
                showRecoveryMessage('Session recovered! Your simulation is still running.');
            }
            
            simulationState.isRunning = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            loadingSpinner.style.display = 'flex';
            vizPlaceholder.style.display = 'none';
            
            // Continue with SSE instead of polling
            listenForSimulationUpdates();
            
        } else if (status.total_frames > 0) {
            // Simulation completed while we were gone - restore results
            statusText.textContent = 'Restoring previous results...';
            statusIndicator.className = 'status-dot complete';
            
            if (status.recovered) {
                showRecoveryMessage('Session recovered! Your simulation results are ready.');
            }
            
            simulationState.totalFrames = status.total_frames;
            simulationState.currentFrame = 0;
            
            // Enable frame controls
            prevFrameBtn.disabled = false;
            playPauseBtn.disabled = false;
            nextFrameBtn.disabled = false;
            
            // Load first frame
            await loadFrame(0);
            
            // Display results
            displayResults();
            
            // Load convergence plot
            loadConvergencePlot();
            
            progressFill.style.width = '100%';
            statusText.textContent = 'Results restored';
        }
    } catch (error) {
        console.error('Error checking existing session:', error);
    }
}

// Show recovery message
function showRecoveryMessage(message) {
    const recoveryBanner = document.createElement('div');
    recoveryBanner.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #4CAF50;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        animation: slideDown 0.3s ease;
    `;
    recoveryBanner.textContent = message;
    document.body.appendChild(recoveryBanner);
    
    // Remove after 4 seconds
    setTimeout(() => {
        recoveryBanner.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => recoveryBanner.remove(), 300);
    }, 4000);
}

async function startSimulation() {
    // Gather parameters
    const paramValues = {};
    for (let key in params) {
        paramValues[key] = parseFloat(params[key].value);
    }
    
    // Update UI
    startBtn.disabled = true;
    stopBtn.disabled = false;
    statusText.textContent = 'Starting simulation...';
    statusIndicator.className = 'status-dot running';
    loadingSpinner.style.display = 'flex';
    vizPlaceholder.style.display = 'none';
    resultsPanel.style.display = 'none';
    convergenceSection.style.display = 'none';
    
    try {
        // Start simulation
        const response = await fetch('/api/start_simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(paramValues)
        });
        
        const data = await response.json();
        
        if (data.success) {
            simulationState.isRunning = true;
            statusText.textContent = 'Simulation running...';
            statusIndicator.className = 'status-dot running';
            
            // Start listening for SSE updates instead of polling
            listenForSimulationUpdates();
        } else {
            statusText.textContent = 'Error: ' + data.message;
            resetUI();
        }
    } catch (error) {
        console.error('Error starting simulation:', error);
        statusText.textContent = 'Error starting simulation';
        resetUI();
    }
}

// Listen for Server-Sent Events (SSE) updates
function listenForSimulationUpdates() {
    const eventSource = new EventSource('/api/simulation_stream');
    
    // Started event
    eventSource.addEventListener('started', (event) => {
        const data = JSON.parse(event.data);
        statusText.textContent = 'Optimization started...';
        progressFill.style.width = '0%';
    });
    
    // Progress events (sent every 5 iterations)
    eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        const progress = data.progress_percent;
        progressFill.style.width = progress + '%';
        statusText.textContent = `Running: Iteration ${data.iteration}/${data.max_iter} | Fitness: ${data.best_fitness.toFixed(6)}`;
    });
    
    // Optimization complete, generating frames
    eventSource.addEventListener('optimization_complete', (event) => {
        const data = JSON.parse(event.data);
        statusText.textContent = 'Generating visualization frames...';
        progressFill.style.width = '95%';
    });
    
    // Generating frames
    eventSource.addEventListener('generating_frames', (event) => {
        statusText.textContent = 'Creating animation frames...';
    });
    
    // Complete event
    eventSource.addEventListener('complete', async (event) => {
        const data = JSON.parse(event.data);
        eventSource.close();  // Stop listening
        
        // Update state
        simulationState.totalFrames = data.total_frames;
        simulationState.isRunning = false;
        
        // Show completion
        await onSimulationComplete();
    });
    
    // Heartbeat (keep-alive)
    eventSource.addEventListener('heartbeat', (event) => {
        // Just keep connection alive, no action needed
    });
    
    // Error handling
    eventSource.addEventListener('error', (error) => {
        console.error('SSE error:', error);
        eventSource.close();
        
        // Fallback to single status check
        setTimeout(async () => {
            try {
                const response = await fetch('/api/simulation_status');
                const status = await response.json();
                
                if (!status.is_running && status.total_frames > 0) {
                    simulationState.totalFrames = status.total_frames;
                    simulationState.isRunning = false;
                    await onSimulationComplete();
                } else if (!status.is_running) {
                    statusText.textContent = 'Simulation failed';
                    resetUI();
                }
            } catch (e) {
                console.error('Error checking status:', e);
                statusText.textContent = 'Connection error';
                resetUI();
            }
        }, 1000);
    });
    
    // Store event source for cleanup
    simulationState.eventSource = eventSource;
}

// Simulation complete
async function onSimulationComplete() {
    simulationState.isRunning = false;
    statusText.textContent = 'Simulation complete!';
    statusIndicator.className = 'status-dot complete';
    progressFill.style.width = '100%';
    loadingSpinner.style.display = 'none';
    
    // Get results
    try {
        const response = await fetch('/api/simulation_status');
        const status = await response.json();
        
        simulationState.totalFrames = status.total_frames;
        simulationState.currentFrame = 0;
        
        // Enable frame controls
        prevFrameBtn.disabled = false;
        playPauseBtn.disabled = false;
        nextFrameBtn.disabled = false;
        
        // Load first frame
        await loadFrame(0);
        
        // Display results
        displayResults();
        
        // Load convergence plot
        loadConvergencePlot();
        
    } catch (error) {
        console.error('Error loading results:', error);
        statusText.textContent = 'Error loading results';
    }
    
    resetUI();
}

// Load specific frame (Canvas version)
async function loadFrame(frameNum) {
    console.log('[loadFrame] Loading frame:', frameNum);
    try {
        const response = await fetch(`/api/get_frame_data/${frameNum}`);
        console.log('[loadFrame] Response status:', response.status);
        const data = await response.json();
        console.log('[loadFrame] Data received:', data);
        
        if (data.success) {
            // Draw frame on canvas
            drawFrame(data);
            
            // Show canvas, hide placeholder
            canvas.style.display = 'block';
            vizPlaceholder.style.display = 'none';
            
            simulationState.currentFrame = frameNum;
            frameCounter.textContent = `Frame ${frameNum + 1} / ${data.total_frames}`;
            
            // Update progress
            const progress = ((frameNum + 1) / data.total_frames) * 100;
            progressFill.style.width = progress + '%';
        } else {
            console.error('[loadFrame] Data success false:', data.message);
        }
    } catch (error) {
        console.error('Error loading frame:', error);
    }
}

// Change frame
function changeFrame(delta) {
    const newFrame = simulationState.currentFrame + delta;
    
    if (newFrame >= 0 && newFrame < simulationState.totalFrames) {
        loadFrame(newFrame);
    }
}

// Toggle play/pause
function togglePlayPause() {
    if (simulationState.isPlaying) {
        // Pause
        clearInterval(simulationState.playInterval);
        simulationState.isPlaying = false;
        playPauseBtn.innerHTML = '<img src="/static/start.png" alt="Play">';
    } else {
        // Play
        simulationState.isPlaying = true;
        playPauseBtn.innerHTML = '<img src="/static/stop.png" alt="Pause">';
        
        simulationState.playInterval = setInterval(() => {
            if (simulationState.currentFrame < simulationState.totalFrames - 1) {
                changeFrame(1);
            } else {
                // Loop back to start
                loadFrame(0);
            }
        }, 200); // 5 fps
    }
}

// Display results
async function displayResults() {
    try {
        const response = await fetch('/api/get_results');
        const data = await response.json();
        
        if (data.success) {
            const fitness = data.best_fitness;
            const position = data.best_position;
            
            // Calculate distance to optimum (0, 0)
            const distance = Math.sqrt(position[0]**2 + position[1]**2);
            
            document.getElementById('result-fitness').textContent = fitness.toFixed(6);
            document.getElementById('result-position').textContent = 
                `(${position[0].toFixed(4)}, ${position[1].toFixed(4)})`;
            document.getElementById('result-distance').textContent = distance.toFixed(6);
            
            resultsPanel.style.display = 'block';
        }
    } catch (error) {
        console.error('Error displaying results:', error);
    }
}

// Load convergence plot (SVG version)
async function loadConvergencePlot() {
    try {
        const response = await fetch('/api/get_convergence_svg');
        
        if (response.ok) {
            const svgText = await response.text();
            convergenceContainer.innerHTML = svgText;
            convergenceSection.style.display = 'block';
        } else {
            console.error('Failed to load convergence plot');
        }
    } catch (error) {
        console.error('Error loading convergence plot:', error);
    }
}

// Stop simulation
function stopSimulation() {
    // Close SSE connection if exists
    if (simulationState.eventSource) {
        simulationState.eventSource.close();
        simulationState.eventSource = null;
    }
    
    simulationState.isRunning = false;
    statusText.textContent = 'Simulation stopped';
    statusIndicator.className = 'status-dot ready';
    resetUI();
}

// Reset simulation
function resetSimulation() {
    // Stop playback
    if (simulationState.isPlaying) {
        togglePlayPause();
    }
    
    // Close SSE if active
    if (simulationState.eventSource) {
        simulationState.eventSource.close();
        simulationState.eventSource = null;
    }
    
    // Reset state
    simulationState = {
        isRunning: false,
        currentFrame: 0,
        totalFrames: 0,
        isPlaying: false,
        playInterval: null,
        sessionId: null,
        wasRecovered: false,
        eventSource: null
    };
    
    // Reset UI - hide canvas instead of image
    canvas.style.display = 'none';
    vizPlaceholder.style.display = 'block';
    resultsPanel.style.display = 'none';
    convergenceSection.style.display = 'none';
    statusText.textContent = 'Ready to start';
    statusIndicator.className = 'status-dot ready';
    progressFill.style.width = '0%';
    frameCounter.textContent = 'Frame 0 / 0';
    
    // Disable controls
    prevFrameBtn.disabled = true;
    playPauseBtn.disabled = true;
    nextFrameBtn.disabled = true;
    
    // Enable start
    startBtn.disabled = false;
    stopBtn.disabled = true;
}

// Reset UI state
function resetUI() {
    startBtn.disabled = false;
    stopBtn.disabled = true;
}

// Initialize
console.log('CSO Visual Simulator initialized');
