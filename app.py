"""
Flask Web Application for CSO Visual Simulator

This app provides a web interface to:
- Configure CSO parameters
- Run simulations
- Visualize cat movements on Rastrigin landscape
- Display convergence curves
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import threading
from datetime import datetime

from cso import CatSwarmOptimizer
from rastrigin import rastrigin
from visualizer import CSOVisualizer


app = Flask(__name__)

# Global state
current_simulation = None
simulation_lock = threading.Lock()
simulation_running = False


class SimulationManager:
    """Manages simulation state and execution."""
    
    def __init__(self):
        self.optimizer = None
        self.visualizer = None
        self.results = None
        self.frame_paths = []
        self.is_running = False
        self.current_frame = 0
        self.total_frames = 0
        self.convergence_path = None
    
    def run_simulation(self, params):
        """
        Execute CSO simulation with given parameters.
        
        Parameters:
        -----------
        params : dict
            Simulation parameters
        """
        self.is_running = True
        
        # Clean previous frames
        visualizer = CSOVisualizer(rastrigin.evaluate, bounds=(-5.12, 5.12))
        visualizer.clean_frames()
        
        # Initialize optimizer
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
        
        # Run optimization
        self.results = self.optimizer.optimize(verbose=True)
        
        # Create visualizer
        self.visualizer = visualizer
        
        # Generate frames
        print("Generating visualization frames...")
        self.frame_paths = self.visualizer.create_animation_frames(
            self.results['history'],
            output_dir='static/frames',
            frame_prefix='frame'
        )
        
        # Generate convergence plot
        self.convergence_path = 'static/frames/convergence.png'
        self.visualizer.plot_convergence(
            self.results['history'],
            save_path=self.convergence_path
        )
        
        self.total_frames = len(self.frame_paths)
        self.current_frame = 0
        self.is_running = False
        
        print(f"Simulation complete! Generated {self.total_frames} frames.")


# Global simulation manager
sim_manager = SimulationManager()


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/api/start_simulation', methods=['POST'])
def start_simulation():
    """Start a new simulation with provided parameters."""
    global simulation_running
    
    if simulation_running:
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
    
    # Run simulation in background thread
    simulation_running = True
    thread = threading.Thread(target=run_simulation_thread, args=(params,))
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Simulation started'
    })


def run_simulation_thread(params):
    """Background thread for running simulation."""
    global simulation_running
    
    try:
        sim_manager.run_simulation(params)
    except Exception as e:
        print(f"Simulation error: {e}")
    finally:
        simulation_running = False


@app.route('/api/simulation_status')
def simulation_status():
    """Get current simulation status."""
    return jsonify({
        'running': simulation_running,
        'total_frames': sim_manager.total_frames,
        'current_frame': sim_manager.current_frame,
        'best_fitness': sim_manager.results['best_fitness'] if sim_manager.results else None,
        'best_position': sim_manager.results['best_position'].tolist() if sim_manager.results else None
    })


@app.route('/api/get_frame/<int:frame_num>')
def get_frame(frame_num):
    """Get specific frame information."""
    if frame_num >= sim_manager.total_frames:
        return jsonify({
            'success': False,
            'message': 'Frame not available'
        }), 404
    
    # Extract frame filename from path
    frame_path = sim_manager.frame_paths[frame_num]
    frame_filename = os.path.basename(frame_path)
    
    # Get fitness at this iteration
    fitness = sim_manager.results['history']['global_best_fitness'][frame_num]
    
    return jsonify({
        'success': True,
        'frame_url': f'/static/frames/{frame_filename}',
        'frame_num': frame_num,
        'total_frames': sim_manager.total_frames,
        'fitness': fitness
    })


@app.route('/api/get_convergence')
def get_convergence():
    """Get convergence plot."""
    if sim_manager.convergence_path and os.path.exists(sim_manager.convergence_path):
        return jsonify({
            'success': True,
            'url': '/' + sim_manager.convergence_path
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Convergence plot not available'
        }), 404


@app.route('/api/get_results')
def get_results():
    """Get final simulation results."""
    if sim_manager.results is None:
        return jsonify({
            'success': False,
            'message': 'No results available'
        }), 404
    
    return jsonify({
        'success': True,
        'best_fitness': sim_manager.results['best_fitness'],
        'best_position': sim_manager.results['best_position'].tolist(),
        'iterations': sim_manager.results['iterations']
    })


@app.route('/static/frames/<path:filename>')
def serve_frame(filename):
    """Serve frame images."""
    return send_from_directory('static/frames', filename)


if __name__ == '__main__':
    # Ensure static directory exists
    os.makedirs('static/frames', exist_ok=True)
    
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
