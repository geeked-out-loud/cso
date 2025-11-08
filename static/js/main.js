// CSO Visual Simulator - Main JavaScript

// State management
let simulationState = {
    isRunning: false,
    currentFrame: 0,
    totalFrames: 0,
    isPlaying: false,
    playInterval: null,
    sessionId: null,
    wasRecovered: false
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
const vizImage = document.getElementById('viz-image');
const vizPlaceholder = document.getElementById('viz-placeholder');
const loadingSpinner = document.getElementById('loading-spinner');
const resultsPanel = document.getElementById('results-panel');
const convergenceSection = document.getElementById('convergence-section');
const convergencePlot = document.getElementById('convergence-plot');

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
            
            // Continue polling
            pollSimulationStatus();
            
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
            
            // Poll for status
            pollSimulationStatus();
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

// Poll simulation status
function pollSimulationStatus() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/simulation_status');
            const status = await response.json();
            
            if (!status.running && simulationState.isRunning) {
                // Simulation completed
                clearInterval(pollInterval);
                onSimulationComplete();
            } else if (status.running) {
                // Update progress
                const progress = 50; // Indeterminate while running
                progressFill.style.width = progress + '%';
            }
        } catch (error) {
            console.error('Error polling status:', error);
        }
    }, 500);
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

// Load specific frame
async function loadFrame(frameNum) {
    try {
        const response = await fetch(`/api/get_frame/${frameNum}`);
        const data = await response.json();
        
        if (data.success) {
            vizImage.src = data.frame_url;
            vizImage.classList.add('active');
            vizPlaceholder.style.display = 'none';
            
            simulationState.currentFrame = frameNum;
            frameCounter.textContent = `Frame ${frameNum + 1} / ${data.total_frames}`;
            
            // Update progress
            const progress = ((frameNum + 1) / data.total_frames) * 100;
            progressFill.style.width = progress + '%';
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

// Load convergence plot
async function loadConvergencePlot() {
    try {
        const response = await fetch('/api/get_convergence');
        const data = await response.json();
        
        if (data.success) {
            convergencePlot.src = data.url + '?t=' + Date.now(); // Cache bust
            convergenceSection.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading convergence plot:', error);
    }
}

// Stop simulation
function stopSimulation() {
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
    
    // Reset state
    simulationState = {
        isRunning: false,
        currentFrame: 0,
        totalFrames: 0,
        isPlaying: false,
        playInterval: null
    };
    
    // Reset UI
    vizImage.src = '';
    vizImage.classList.remove('active');
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
