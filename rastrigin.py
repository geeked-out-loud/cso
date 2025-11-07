"""
Rastrigin Function Module

The Rastrigin function is a highly multimodal benchmark test function
used to evaluate optimization algorithms.

Definition:
    f(x) = A*n + sum(x_i^2 - A*cos(2*pi*x_i))
    
Properties:
    - Global minimum: f(0, 0, ..., 0) = 0
    - Domain: x_i ∈ [-5.12, 5.12]
    - Highly multimodal with many local minima
"""

import numpy as np


class RastriginFunction:
    """
    Rastrigin function implementation for optimization benchmarking.
    """
    
    def __init__(self, A=10, bounds=(-5.12, 5.12)):
        """
        Initialize Rastrigin function.
        
        Parameters:
        -----------
        A : float
            Constant parameter (default: 10)
        bounds : tuple
            Search space bounds (min, max) for each dimension
        """
        self.A = A
        self.bounds = bounds
        self.global_minimum = 0.0
        self.optimal_position = None  # Will be set based on dimension
    
    def evaluate(self, x):
        """
        Evaluate Rastrigin function at position x.
        
        Parameters:
        -----------
        x : array-like
            Position vector (can be 1D or 2D array for multiple points)
            
        Returns:
        --------
        float or array
            Function value(s)
        """
        x = np.asarray(x)
        
        # Handle single point vs multiple points
        if x.ndim == 1:
            n = len(x)
            return self.A * n + np.sum(x**2 - self.A * np.cos(2 * np.pi * x))
        else:
            # Multiple points (rows are different positions)
            n = x.shape[1]
            return self.A * n + np.sum(x**2 - self.A * np.cos(2 * np.pi * x), axis=1)
    
    def __call__(self, x):
        """Allow function to be called directly."""
        return self.evaluate(x)
    
    def get_bounds(self, dim):
        """
        Get bounds for specified dimensionality.
        
        Parameters:
        -----------
        dim : int
            Number of dimensions
            
        Returns:
        --------
        list of tuples
            [(min, max), (min, max), ...] for each dimension
        """
        return [self.bounds for _ in range(dim)]
    
    def is_in_bounds(self, x):
        """
        Check if position is within bounds.
        
        Parameters:
        -----------
        x : array-like
            Position vector
            
        Returns:
        --------
        bool
            True if all components are within bounds
        """
        x = np.asarray(x)
        return np.all((x >= self.bounds[0]) & (x <= self.bounds[1]))
    
    def clip_to_bounds(self, x):
        """
        Clip position to bounds.
        
        Parameters:
        -----------
        x : array-like
            Position vector
            
        Returns:
        --------
        array
            Clipped position
        """
        return np.clip(x, self.bounds[0], self.bounds[1])


def rastrigin_2d(x, y, A=10):
    """
    Convenience function for 2D Rastrigin evaluation.
    
    Parameters:
    -----------
    x, y : float or array
        Coordinates
    A : float
        Constant parameter (default: 10)
        
    Returns:
    --------
    float or array
        Function value
    """
    return A * 2 + (x**2 - A * np.cos(2 * np.pi * x)) + (y**2 - A * np.cos(2 * np.pi * y))


# Create default instance
rastrigin = RastriginFunction()
