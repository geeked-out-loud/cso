from flask import Flask, render_template, request, jsonify, send_from_directory, session
import os
import json
import threading
from datetime import datetime
import requests
import secrets
import shutil
import time

from cso import CatSwarmOptimizer
from rastrigin import rastrigin
from visualizer import CSOVisualizer


app = Flask(__name__)

# Secret key for session management (required for Flask sessions)
app.secret_key = secrets.token_hex(16)

# Configure session to be persistent across browser refreshes
app.config['SESSION_COOKIE_NAME'] = 'cso_session'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 7200  # 2 hours

# Global state - now a dictionary of session managers
simulation_managers = {}  # {session_id: SimulationManager}
simulation_locks = {}     # {session_id: threading.Lock}
orphaned_sessions = set()  # Track sessions with running sims but disconnected clients

# Ensure frames directory exists at startup
FRAMES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'frames')
print(f"[STARTUP] Checking frames directory: {FRAMES_DIR}")
try:
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[STARTUP] Frames directory ready")
    # Test write permissions
    test_file = os.path.join(FRAMES_DIR, '.test')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print(f"[STARTUP] Write permissions confirmed")
except Exception as e:
    print(f"[STARTUP] ERROR with frames directory: {e}")
    import traceback
    traceback.print_exc()


class SimulationManager:
    """Manages simulation state and execution for a single session."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.optimizer = None
        self.visualizer = None
        self.results = None
        self.frame_paths = []
        self.is_running = False
        self.current_frame = 0
        self.total_frames = 0
        self.convergence_path = None
        self.last_accessed = time.time()  # For cleanup
        self.created_at = datetime.now()
    
    def mark_accessed(self):
        """Update last access timestamp."""
        self.last_accessed = time.time()
    
    def run_simulation(self, params):
        """
        Execute CSO simulation with given parameters.
        
        Parameters:
        -----------
        params : dict
            Simulation parameters
        """
        try:
            self.is_running = True
            self.mark_accessed()
            
            # Session-specific output directory
            output_dir = f'static/frames/{self.session_id}'
            print(f"[Session {self.session_id}] Creating directory: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
            print(f"[Session {self.session_id}] Directory created successfully")
            
            # Clean previous frames for THIS session
            print(f"[Session {self.session_id}] Initializing visualizer...")
            visualizer = CSOVisualizer(rastrigin.evaluate, bounds=(-5.12, 5.12))
            visualizer.clean_frames(output_dir=output_dir)
            print(f"[Session {self.session_id}] Cleaned previous frames")
            
            # Initialize optimizer
            print(f"[Session {self.session_id}] Initializing optimizer with params: {params}")
            self.optimizer = CatSwarmOptimizer(
                fitness_func=rastrigin.evaluate,
                dim=2,
                n_cats=params.get('n_cats', 30),
                max_iter=params.get('max_iter', 50),
                MR=params.get('MR', 0.3),
                SMP=params.get('SMP', 5),
                SRD=params.get('SRD', 0.2),
                CDC=params.get('CDC', 0.8),
                c1=params.get('c1', 2.0),
                w=params.get('w', 0.5),
                bounds=(-5.12, 5.12)
            )
            print(f"[Session {self.session_id}] Optimizer initialized")
            
            # Run optimization
            print(f"[Session {self.session_id}] Starting optimization...")
            self.results = self.optimizer.optimize(verbose=True)
            print(f"[Session {self.session_id}] Optimization complete")
            
            # Create visualizer
            self.visualizer = visualizer
            
            # Generate frames in session-specific directory
            print(f"[Session {self.session_id}] Generating visualization frames...")
            self.frame_paths = self.visualizer.create_animation_frames(
                self.results['history'],
                output_dir=output_dir,
                frame_prefix='frame'
            )
            print(f"[Session {self.session_id}] Generated {len(self.frame_paths)} frames")
            
            # Generate convergence plot in session-specific directory
            self.convergence_path = f'{output_dir}/convergence.png'
            print(f"[Session {self.session_id}] Creating convergence plot...")
            self.visualizer.plot_convergence(
                self.results['history'],
                save_path=self.convergence_path
            )
            print(f"[Session {self.session_id}] Convergence plot created")
            
            self.total_frames = len(self.frame_paths)
            self.current_frame = 0
            self.is_running = False
            self.mark_accessed()
            
            print(f"[Session {self.session_id}] Simulation complete! Generated {self.total_frames} frames.")
            
        except Exception as e:
            print(f"[Session {self.session_id}] FATAL ERROR in run_simulation: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False
            raise


def get_or_create_session_id():
    """Get existing session ID or create new one."""
    if 'user_id' not in session:
        session['user_id'] = secrets.token_hex(8)
        session.permanent = True  # Make session persistent
        print(f"[Session] Created new session: {session['user_id']}")
    else:
        # Reactivate session if it was orphaned
        session_id = session['user_id']
        if session_id in orphaned_sessions:
            orphaned_sessions.discard(session_id)
            print(f"[Session] Reactivated orphaned session: {session_id}")
    return session['user_id']


def get_session_manager():
    """Get or create SimulationManager for current session."""
    session_id = get_or_create_session_id()
    
    if session_id not in simulation_managers:
        simulation_managers[session_id] = SimulationManager(session_id)
        simulation_locks[session_id] = threading.Lock()
        print(f"[Session] Created new manager for session: {session_id}")
    
    # Mark as accessed
    simulation_managers[session_id].mark_accessed()
    
    return simulation_managers[session_id]


def cleanup_old_sessions():
    """Background thread to cleanup inactive sessions."""
    while True:
        time.sleep(1800)  # Run every 30 minutes
        current_time = time.time()
        timeout = 7200  # 2 hours
        
        sessions_to_remove = []
        
        for session_id, manager in list(simulation_managers.items()):
            # If inactive for > 2 hours and not running
            if (current_time - manager.last_accessed > timeout and 
                not manager.is_running):
                sessions_to_remove.append(session_id)
            # Mark as orphaned if running but not accessed recently (30 min)
            elif manager.is_running and (current_time - manager.last_accessed > 1800):
                if session_id not in orphaned_sessions:
                    orphaned_sessions.add(session_id)
                    print(f"[Cleanup] Marked session as orphaned: {session_id}")
        
        # Remove old sessions
        for session_id in sessions_to_remove:
            try:
                # Delete files
                output_dir = f'static/frames/{session_id}'
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
                    print(f"[Cleanup] Deleted frames for session: {session_id}")
                
                # Remove from memory
                del simulation_managers[session_id]
                if session_id in simulation_locks:
                    del simulation_locks[session_id]
                if session_id in orphaned_sessions:
                    orphaned_sessions.discard(session_id)
                print(f"[Cleanup] Removed session: {session_id}")
            except Exception as e:
                print(f"[Cleanup] Error removing session {session_id}: {e}")


def keep_alive():
    """Keep the application alive."""
    while True:
        time.sleep(600)
        try:
            if os.getenv('RENDER_EXTERNAL_URL'):
                url = os.getenv('RENDER_EXTERNAL_URL')
                response = requests.get(url, timeout=10)
                print(f"[Keep-Alive] Pinged {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"[Keep-Alive] Ping failed: {e}")

@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/api/start_simulation', methods=['POST'])
def start_simulation():
    """Start a new simulation with provided parameters."""
    manager = get_session_manager()
    session_id = session['user_id']
    
    if manager.is_running:
        return jsonify({
            'success': False,
            'message': 'Simulation already running'
        }), 400
    
    # Get parameters from request
    params = request.json
    
    # Validate parameters
    try:
        params = {
            'n_cats': int(params.get('n_cats', 30)),
            'max_iter': int(params.get('max_iter', 50)),
            'MR': float(params.get('MR', 0.3)),
            'SMP': int(params.get('SMP', 5)),
            'SRD': float(params.get('SRD', 0.2)),
            'CDC': float(params.get('CDC', 0.8)),
            'c1': float(params.get('c1', 2.0)),
            'w': float(params.get('w', 0.5))
        }
    except (ValueError, TypeError) as e:
        return jsonify({
            'success': False,
            'message': f'Invalid parameters: {str(e)}'
        }), 400
    
    # Ensure lock exists for this session
    if session_id not in simulation_locks:
        simulation_locks[session_id] = threading.Lock()
    
    # Run simulation in background thread for this session
    print(f"[Session {session_id}] Starting background thread with params: {params}")
    
    def run_with_error_handling():
        """Wrapper to catch any thread errors."""
        try:
            print(f"[Session {session_id}] Thread executing...")
            manager.run_simulation(params)
            print(f"[Session {session_id}] Thread completed successfully")
        except Exception as e:
            print(f"[Session {session_id}] Thread error: {e}")
            import traceback
            traceback.print_exc()
            manager.is_running = False
    
    thread = threading.Thread(target=run_with_error_handling)
    thread.daemon = True
    thread.start()
    print(f"[Session {session_id}] Background thread started")
    
    return jsonify({
        'success': True,
        'message': 'Simulation started'
    })


@app.route('/api/simulation_status')
def simulation_status():
    """Get current simulation status."""
    manager = get_session_manager()
    session_id = session.get('user_id')
    
    # Check if this session was orphaned and recovered
    was_orphaned = session_id in orphaned_sessions if session_id else False
    
    return jsonify({
        'is_running': manager.is_running,
        'total_frames': manager.total_frames,
        'current_frame': manager.current_frame,
        'best_fitness': manager.results['best_fitness'] if manager.results else None,
        'best_position': manager.results['best_position'].tolist() if manager.results else None,
        'session_id': session_id,
        'recovered': was_orphaned  # Frontend can show recovery message
    })


@app.route('/api/get_frame/<int:frame_num>')
def get_frame(frame_num):
    """Get specific frame information."""
    manager = get_session_manager()
    
    if frame_num >= manager.total_frames:
        return jsonify({
            'success': False,
            'message': 'Frame not available'
        }), 404
    
    # Extract frame filename from path
    frame_path = manager.frame_paths[frame_num]
    
    # Get fitness at this iteration
    fitness = manager.results['history']['global_best_fitness'][frame_num]
    
    # Return session-specific frame URL
    return jsonify({
        'success': True,
        'frame_url': f'/{frame_path}',
        'frame_num': frame_num,
        'total_frames': manager.total_frames,
        'fitness': fitness
    })


@app.route('/api/get_convergence')
def get_convergence():
    """Get convergence plot."""
    manager = get_session_manager()
    
    if manager.convergence_path and os.path.exists(manager.convergence_path):
        return jsonify({
            'success': True,
            'url': '/' + manager.convergence_path
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Convergence plot not available'
        }), 404


@app.route('/api/get_results')
def get_results():
    """Get final simulation results."""
    manager = get_session_manager()
    
    if manager.results is None:
        return jsonify({
            'success': False,
            'message': 'No results available'
        }), 404
    
    return jsonify({
        'success': True,
        'best_fitness': manager.results['best_fitness'],
        'best_position': manager.results['best_position'].tolist(),
        'iterations': manager.results['iterations']
    })


@app.route('/static/frames/<session_id>/<path:filename>')
def serve_frame(session_id, filename):
    """Serve frame images from session-specific directory."""
    directory = f'static/frames/{session_id}'
    if not os.path.exists(directory):
        return jsonify({'error': 'Session not found'}), 404
    return send_from_directory(directory, filename)


if __name__ == '__main__':
    # Ensure static directory exists
    os.makedirs('static/frames', exist_ok=True)
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
    cleanup_thread.start()
    print("[Cleanup] Session cleanup thread started.")

    # Keep Alive Thread (for Render deployment)
    if os.getenv("RENDER"):
        keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        keep_alive_thread.start()
        print("[Keep-Alive] Thread started.")

    print("\n" + "="*60)
    print("CSO Visual Simulator - Cat Swarm Optimization")
    print("="*60)
    print("\nStarting Flask server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server.")
    print("="*60 + "\n")
    
    # Get port from environment variable (for deployment) or use 5000 for local
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
