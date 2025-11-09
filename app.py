from flask import Flask, render_template, request, jsonify, send_from_directory, session, Response, stream_with_context
import os
import json
import threading
from datetime import datetime
import requests
import secrets
import shutil
import time
import queue

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


class SimulationManager:
    """Manages simulation state and execution for a single session."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.optimizer = None
        self.visualizer = None
        self.results = None
        self.frame_data = []  # Changed from frame_paths to frame_data (JSON)
        self.is_running = False
        self.current_frame = 0
        self.total_frames = 0
        self.convergence_svg = None  # Changed from convergence_path to SVG string
        self.visualization_ready = False  # Track if visualization is complete
        self.last_accessed = time.time()  # For cleanup
        self.created_at = datetime.now()
        self.event_queue = queue.Queue()  # For SSE updates
    
    def send_update(self, event_type, data):
        """Send update to client via Server-Sent Events."""
        self.event_queue.put({
            'event': event_type,
            'data': data
        })
    
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
            
            # No longer need session-specific output directory (no files!)
            print(f"[Session {self.session_id}] Initializing visualizer...")
            visualizer = CSOVisualizer(rastrigin.evaluate, bounds=(-5.12, 5.12))
            print(f"[Session {self.session_id}] Visualizer initialized")
            
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
            
            # Send started event
            self.send_update('started', {
                'message': 'Optimization started',
                'max_iter': params.get('max_iter', 50)
            })
            
            # Define progress callback for SSE updates
            def on_progress(iteration, max_iter, best_fitness):
                self.send_update('progress', {
                    'iteration': iteration,
                    'max_iter': max_iter,
                    'best_fitness': float(best_fitness),
                    'progress_percent': int((iteration / max_iter) * 100)
                })
            
            # Run optimization with progress callback
            self.results = self.optimizer.optimize(verbose=True, progress_callback=on_progress)
            print(f"[Session {self.session_id}] Optimization complete")
            
            # Send optimization complete event
            self.send_update('optimization_complete', {
                'message': 'Optimization complete, generating visualization...',
                'best_fitness': float(self.results['best_fitness'])
            })
            
            # Mark visualization as NOT ready yet (optimization complete but frames not generated)
            self.visualization_ready = False
            
            # Create visualizer
            self.visualizer = visualizer
            
            # Prepare frame data (no file generation!)
            print(f"[Session {self.session_id}] Preparing frame data for client-side rendering...")
            self.send_update('generating_frames', {
                'message': 'Preparing visualization data...'
            })
            
            self.frame_data = self.visualizer.prepare_frame_data(
                self.results['history']
            )
            print(f"[Session {self.session_id}] Prepared {len(self.frame_data)} frames")
            
            # Generate convergence SVG (no file saving!)
            print(f"[Session {self.session_id}] Creating convergence SVG...")
            self.convergence_svg = self.visualizer.create_convergence_svg(
                self.results['history']
            )
            print(f"[Session {self.session_id}] Convergence SVG created")
            
            self.total_frames = len(self.frame_data)
            self.current_frame = 0
            
            # NOW mark visualization as ready (all frames generated)
            self.visualization_ready = True
            
            self.is_running = False
            self.mark_accessed()
            
            # Send completion event
            self.send_update('complete', {
                'message': 'Simulation complete!',
                'total_frames': self.total_frames,
                'best_fitness': float(self.results['best_fitness']),
                'best_position': self.results['best_position'].tolist()
            })
            
            print(f"[Session {self.session_id}] Simulation complete! Generated {self.total_frames} frames.")
            
        except Exception as e:
            print(f"[Session {self.session_id}] FATAL ERROR in run_simulation: {e}")
            import traceback
            traceback.print_exc()
            self.visualization_ready = False
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
    
    # Only return results and frame count when visualization is ready
    # This prevents race condition where optimization completes but frames aren't generated yet
    has_results = manager.results is not None and manager.visualization_ready
    
    return jsonify({
        'is_running': manager.is_running,
        'total_frames': manager.total_frames if manager.visualization_ready else 0,
        'current_frame': manager.current_frame,
        'best_fitness': manager.results['best_fitness'] if has_results else None,
        'best_position': manager.results['best_position'].tolist() if has_results else None,
        'session_id': session_id,
        'recovered': was_orphaned  # Frontend can show recovery message
    })


@app.route('/api/simulation_stream')
def simulation_stream():
    """Server-Sent Events stream for real-time simulation updates."""
    print("[SSE] simulation_stream endpoint called")
    try:
        session_id = session.get('user_id')
        print(f"[SSE] Session ID: {session_id}")
        
        manager = get_session_manager()
        print(f"[SSE] Got manager for session: {manager.session_id}")
        
        def event_stream():
            """Generate SSE events from the simulation."""
            try:
                # Send initial connection event
                print(f"[SSE] Sending connected event")
                yield f"event: connected\n"
                yield f"data: {json.dumps({'message': 'Connected to simulation stream'})}\n\n"
                
                while True:
                    try:
                        # Wait for event with timeout
                        event = manager.event_queue.get(timeout=30)
                        
                        # Format as SSE
                        event_type = event['event']
                        event_data = json.dumps(event['data'])
                        
                        yield f"event: {event_type}\n"
                        yield f"data: {event_data}\n\n"
                        
                        # Stop stream if simulation complete
                        if event_type == 'complete':
                            break
                            
                    except queue.Empty:
                        # Send heartbeat every 30s to keep connection alive
                        yield f"event: heartbeat\n"
                        yield f"data: {{}}\n\n"
                        
            except GeneratorExit:
                # Client disconnected
                print(f"[Session {manager.session_id}] SSE client disconnected")
            except Exception as e:
                # Error in stream
                print(f"[Session {manager.session_id}] SSE stream error: {e}")
                yield f"event: error\n"
                yield f"data: {json.dumps({'message': str(e)})}\n\n"
        
        return Response(
            stream_with_context(event_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )
    except Exception as e:
        print(f"[SSE] Error creating stream: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create event stream', 'message': str(e)}), 500


@app.route('/api/get_frame_data/<int:frame_num>')
def get_frame_data(frame_num):
    """Get frame data as JSON for client-side Canvas rendering."""
    try:
        manager = get_session_manager()
        
        if not manager.frame_data or frame_num >= len(manager.frame_data):
            return jsonify({
                'success': False,
                'message': 'Frame not available'
            }), 404
        
        frame = manager.frame_data[frame_num]
        
        # Convert numpy arrays to lists for JSON serialization
        import numpy as np
        
        def to_list(obj):
            """Convert numpy array to list, or return as-is if already a list."""
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, list):
                # Handle list of numpy arrays
                return [to_list(item) for item in obj]
            return obj
        
        try:
            response_data = {
                'success': True,
                'iteration': int(frame['iteration']),
                'positions': to_list(frame['positions']),
                'modes': to_list(frame['modes']) if isinstance(frame['modes'], np.ndarray) else list(frame['modes']),
                'fitnesses': to_list(frame['fitnesses']),
                'global_best_fitness': float(frame['global_best_fitness']),
                'global_best_position': to_list(frame['global_best_position']) if frame['global_best_position'] is not None else [0, 0],
                'frame_num': int(frame_num),
                'total_frames': int(manager.total_frames)
            }
        except Exception as conv_error:
            print(f"[API] ERROR converting frame data: {conv_error}")
            print(f"[API] Frame keys: {frame.keys()}")
            for key, value in frame.items():
                print(f"[API]   {key}: type={type(value)}, shape={getattr(value, 'shape', 'N/A')}")
            raise
        
        print(f"[API] Sending frame {frame_num} data - iteration: {response_data['iteration']}, positions: {len(response_data['positions'])}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[API] ERROR in get_frame_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/get_convergence_svg')
def get_convergence_svg():
    """Get convergence plot as SVG."""
    manager = get_session_manager()
    
    if manager.convergence_svg:
        return Response(
            manager.convergence_svg,
            mimetype='image/svg+xml',
            headers={
                'Cache-Control': 'no-cache',
                'Content-Type': 'image/svg+xml'
            }
        )
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


if __name__ == '__main__':
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
