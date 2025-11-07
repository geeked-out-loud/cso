"""
Visualization Module for CSO Simulation

Generates 2D contour plots of the Rastrigin function with cat positions
overlaid, distinguishing between seeking and tracing modes.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Flask
import matplotlib.pyplot as plt
from matplotlib import cm
import os


class CSOVisualizer:
    """
    Visualizer for Cat Swarm Optimization on 2D functions.
    """
    
    def __init__(self, fitness_func, bounds=(-5.12, 5.12), resolution=200):
        """
        Initialize visualizer.
        
        Parameters:
        -----------
        fitness_func : callable
            Function to visualize (should accept x, y coordinates)
        bounds : tuple
            (min, max) bounds for plotting
        resolution : int
            Grid resolution for contour plot
        """
        self.fitness_func = fitness_func
        self.bounds = bounds
        self.resolution = resolution
        
        # Create meshgrid for contour plot
        x = np.linspace(bounds[0], bounds[1], resolution)
        y = np.linspace(bounds[0], bounds[1], resolution)
        self.X, self.Y = np.meshgrid(x, y)
        
        # Evaluate function on grid
        self.Z = self._evaluate_grid()
        
        # Setup plot style
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def _evaluate_grid(self):
        """Evaluate fitness function on meshgrid."""
        Z = np.zeros_like(self.X)
        for i in range(self.X.shape[0]):
            for j in range(self.X.shape[1]):
                Z[i, j] = self.fitness_func(np.array([self.X[i, j], self.Y[i, j]]))
        return Z
    
    def plot_frame(self, positions, modes, global_best_pos, iteration, 
                   fitness_value, save_path=None, show_trajectory=False):
        """
        Generate a single frame showing cat positions on Rastrigin landscape.
        
        Parameters:
        -----------
        positions : array-like
            Cat positions, shape (n_cats, 2)
        modes : list
            Mode for each cat ('seeking' or 'tracing')
        global_best_pos : array-like
            Global best position
        iteration : int
            Current iteration number
        fitness_value : float
            Current best fitness value
        save_path : str
            Path to save image (if None, returns figure)
        show_trajectory : bool
            Whether to show trajectory lines (for future enhancement)
            
        Returns:
        --------
        str or Figure
            Save path or matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot contour
        contour = ax.contourf(self.X, self.Y, self.Z, levels=30, 
                             cmap='viridis', alpha=0.7)
        ax.contour(self.X, self.Y, self.Z, levels=15, 
                  colors='black', alpha=0.2, linewidths=0.5)
        
        # Add colorbar
        cbar = plt.colorbar(contour, ax=ax)
        cbar.set_label('Fitness Value', rotation=270, labelpad=20)
        
        # Separate cats by mode
        positions = np.array(positions)
        seeking_cats = positions[[i for i, m in enumerate(modes) if m == 'seeking']]
        tracing_cats = positions[[i for i, m in enumerate(modes) if m == 'tracing']]
        
        # Plot seeking cats (blue circles)
        if len(seeking_cats) > 0:
            ax.scatter(seeking_cats[:, 0], seeking_cats[:, 1], 
                      c='blue', marker='o', s=100, alpha=0.8,
                      edgecolors='white', linewidths=1.5, 
                      label=f'Seeking ({len(seeking_cats)} cats)', zorder=5)
        
        # Plot tracing cats (red triangles)
        if len(tracing_cats) > 0:
            ax.scatter(tracing_cats[:, 0], tracing_cats[:, 1], 
                      c='red', marker='^', s=120, alpha=0.8,
                      edgecolors='white', linewidths=1.5,
                      label=f'Tracing ({len(tracing_cats)} cats)', zorder=5)
        
        # Plot global best (gold star)
        ax.scatter(global_best_pos[0], global_best_pos[1], 
                  c='gold', marker='*', s=500, alpha=1.0,
                  edgecolors='black', linewidths=2,
                  label='Global Best', zorder=10)
        
        # Plot true optimum (green x)
        ax.scatter(0, 0, c='lime', marker='x', s=200, 
                  linewidths=3, label='True Optimum', zorder=6)
        
        # Labels and title
        ax.set_xlabel('X', fontsize=12, fontweight='bold')
        ax.set_ylabel('Y', fontsize=12, fontweight='bold')
        ax.set_title(f'Cat Swarm Optimization - Iteration {iteration}\n'
                    f'Best Fitness: {fitness_value:.6f}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Legend
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Set bounds
        ax.set_xlim(self.bounds[0], self.bounds[1])
        ax.set_ylim(self.bounds[0], self.bounds[1])
        
        # Tight layout
        plt.tight_layout()
        
        # Save or return
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            return save_path
        else:
            return fig
    
    def create_animation_frames(self, history, output_dir='static/frames', 
                               frame_prefix='frame'):
        """
        Create frames for all iterations in history.
        
        Parameters:
        -----------
        history : dict
            History dict from CSO optimizer
        output_dir : str
            Directory to save frames
        frame_prefix : str
            Prefix for frame filenames
            
        Returns:
        --------
        list
            List of frame file paths
        """
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        frame_paths = []
        n_iterations = len(history['positions'])
        
        for i in range(n_iterations):
            positions = history['positions'][i]
            modes = history['modes'][i]
            fitness = history['global_best_fitness'][i]
            
            # Get global best position at this iteration
            # Find the cat with best fitness
            fitnesses = history['fitnesses'][i]
            best_idx = np.argmin(fitnesses)
            global_best = positions[best_idx]
            
            # Generate frame
            frame_path = os.path.join(output_dir, f'{frame_prefix}_{i:04d}.png')
            self.plot_frame(positions, modes, global_best, i, fitness, 
                          save_path=frame_path)
            frame_paths.append(frame_path)
        
        return frame_paths
    
    def plot_convergence(self, history, save_path=None):
        """
        Plot convergence curve (fitness vs iteration).
        
        Parameters:
        -----------
        history : dict
            History dict from CSO optimizer
        save_path : str
            Path to save plot
            
        Returns:
        --------
        str or Figure
            Save path or Figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        iterations = range(len(history['global_best_fitness']))
        fitness_values = history['global_best_fitness']
        
        # Plot fitness curve
        ax.plot(iterations, fitness_values, 'b-', linewidth=2, 
               label='Best Fitness')
        ax.scatter(iterations, fitness_values, c='blue', s=20, alpha=0.5)
        
        # Horizontal line at optimum
        ax.axhline(y=0, color='green', linestyle='--', linewidth=2, 
                  label='Global Optimum (0)', alpha=0.7)
        
        # Labels
        ax.set_xlabel('Iteration', fontsize=12, fontweight='bold')
        ax.set_ylabel('Best Fitness Value', fontsize=12, fontweight='bold')
        ax.set_title('CSO Convergence Curve', fontsize=14, fontweight='bold')
        
        # Log scale for y-axis if values are very different
        if max(fitness_values) > 100 * min(fitness_values[1:] if len(fitness_values) > 1 else [1]):
            ax.set_yscale('log')
            ax.set_ylabel('Best Fitness Value (log scale)', fontsize=12, fontweight='bold')
        
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            return save_path
        else:
            return fig
    
    def clean_frames(self, output_dir='static/frames'):
        """
        Remove all frame images from directory.
        
        Parameters:
        -----------
        output_dir : str
            Directory containing frames
        """
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith('.png'):
                    os.remove(os.path.join(output_dir, filename))
