"""
Visualization Module for CSO Simulation

Prepares data for client-side Canvas rendering and generates SVG convergence plots.
No longer generates matplotlib PNGs for frames - that's done client-side for performance.
"""

import numpy as np


class CSOVisualizer:
    """
    Visualizer for Cat Swarm Optimization on 2D functions.
    Prepares data for client-side rendering instead of server-side image generation.
    """
    
    def __init__(self, fitness_func, bounds=(-5.12, 5.12)):
        """Initialize visualizer."""
        self.fitness_func = fitness_func
        self.bounds = bounds
    
    def prepare_frame_data(self, history):
        """Prepare frame data for client-side Canvas rendering."""
        print(f"[Visualizer] Preparing frame data for client-side rendering")
        
        frames = []
        n_iterations = len(history['positions'])
        
        frame_indices = set([0])
        frame_indices.add(n_iterations - 1)
        
        for i in range(0, n_iterations, 5):
            frame_indices.add(i)
        
        frame_indices = sorted(list(frame_indices))
        print(f"[Visualizer] Preparing {len(frame_indices)} frames from {n_iterations} iterations")
        
        for i in frame_indices:
            positions = history['positions'][i]
            modes = history['modes'][i]
            fitnesses = history['fitnesses'][i]
            global_best_fitness = history['global_best_fitness'][i]
            
            best_idx = np.argmin(fitnesses)
            global_best_position = positions[best_idx]
            
            frame_data = {
                'iteration': int(i),
                'positions': positions,
                'modes': modes.tolist() if hasattr(modes, 'tolist') else list(modes),
                'fitnesses': fitnesses,
                'global_best_fitness': float(global_best_fitness),
                'global_best_position': global_best_position
            }
            
            frames.append(frame_data)
        
        print(f"[Visualizer] Successfully prepared {len(frames)} frames")
        return frames
    
    def create_convergence_svg(self, history, width=800, height=400):
        """Generate convergence plot as SVG string."""
        print(f"[Visualizer] Creating convergence SVG")
        
        iterations = list(range(len(history['global_best_fitness'])))
        fitness_values = history['global_best_fitness']
        
        max_iter = len(iterations)
        max_fitness = max(fitness_values)
        min_fitness = min(fitness_values[1:] if len(fitness_values) > 1 else [0])
        
        use_log = max_fitness > 100 * min_fitness and min_fitness > 0
        
        margin_left = 80
        margin_right = 40
        margin_top = 50
        margin_bottom = 70
        plot_width = width - margin_left - margin_right
        plot_height = height - margin_top - margin_bottom
        
        def scale_x(iter_num):
            return margin_left + (iter_num / max(max_iter - 1, 1)) * plot_width
        
        def scale_y(fitness):
            if use_log:
                fitness = max(fitness, 0.0001)
                log_min = np.log10(min_fitness) if min_fitness > 0 else -4
                log_max = np.log10(max_fitness)
                log_val = np.log10(fitness)
                normalized = (log_val - log_min) / max(log_max - log_min, 0.001)
            else:
                fitness_range = max_fitness - min_fitness
                normalized = (fitness - min_fitness) / max(fitness_range, 0.001) if fitness_range > 0 else 0
            return margin_top + plot_height - normalized * plot_height
        
        svg_parts = []
        svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
        svg_parts.append(f'<rect width="{width}" height="{height}" fill="#fafafa"/>')
        svg_parts.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_width}" height="{plot_height}" fill="white" stroke="#ddd" stroke-width="2"/>')
        
        for i in range(6):
            y = margin_top + (i / 5) * plot_height
            svg_parts.append(f'<line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" stroke="#eee" stroke-width="1"/>')
        
        for i in range(6):
            x = margin_left + (i / 5) * plot_width
            svg_parts.append(f'<line x1="{x}" y1="{margin_top}" x2="{x}" y2="{height - margin_bottom}" stroke="#eee" stroke-width="1"/>')
        
        points = ' '.join([f'{scale_x(i)},{scale_y(fitness_values[i])}' for i in iterations])
        svg_parts.append(f'<polyline points="{points}" fill="none" stroke="#FF9B71" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
        
        for i in iterations:
            x = scale_x(i)
            y = scale_y(fitness_values[i])
            svg_parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#FF7A47" stroke="white" stroke-width="2"/>')
        
        svg_parts.append(f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#333" stroke-width="2"/>')
        svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#333" stroke-width="2"/>')
        svg_parts.append(f'<text x="{width / 2}" y="{height - 15}" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="14" font-weight="600" fill="#333">Iteration</text>')
        
        y_label = "Fitness (log scale)" if use_log else "Fitness"
        svg_parts.append(f'<text x="20" y="{height / 2}" text-anchor="middle" transform="rotate(-90 20 {height/2})" font-family="Inter, system-ui, sans-serif" font-size="14" font-weight="600" fill="#333">{y_label}</text>')
        svg_parts.append(f'<text x="{width / 2}" y="30" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="#2D2D2D">Convergence Curve</text>')
        
        num_x_ticks = min(6, max_iter + 1)
        for i in range(num_x_ticks):
            iter_val = int((i / max(num_x_ticks - 1, 1)) * (max_iter - 1)) if max_iter > 1 else 0
            x = scale_x(iter_val)
            svg_parts.append(f'<line x1="{x}" y1="{height - margin_bottom}" x2="{x}" y2="{height - margin_bottom + 6}" stroke="#333" stroke-width="2"/>')
            svg_parts.append(f'<text x="{x}" y="{height - margin_bottom + 22}" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="12" fill="#666">{iter_val}</text>')
        
        num_y_ticks = 6
        for i in range(num_y_ticks):
            if use_log and min_fitness > 0:
                log_range = np.log10(max_fitness) - np.log10(min_fitness)
                log_val = np.log10(min_fitness) + (i / (num_y_ticks - 1)) * log_range
                val = 10 ** log_val
                label = f'{val:.2e}'
            else:
                fitness_range = max_fitness - min_fitness
                val = min_fitness + (i / (num_y_ticks - 1)) * fitness_range
                label = f'{val:.4f}' if val < 1 else f'{val:.2f}'
            
            y = margin_top + plot_height - (i / (num_y_ticks - 1)) * plot_height
            svg_parts.append(f'<line x1="{margin_left - 6}" y1="{y}" x2="{margin_left}" y2="{y}" stroke="#333" stroke-width="2"/>')
            svg_parts.append(f'<text x="{margin_left - 10}" y="{y + 4}" text-anchor="end" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#666">{label}</text>')
        
        svg_parts.append('</svg>')
        
        svg_string = '\n'.join(svg_parts)
        print(f"[Visualizer] Convergence SVG created successfully ({len(svg_string)} bytes)")
        return svg_string
