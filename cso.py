"""
Cat Swarm Optimization (CSO) Algorithm

CSO is a population-based metaheuristic optimization algorithm inspired 
by the behavior of cats. Each cat alternates between two modes:
    - Seeking Mode: Exploration (local search with random perturbations)
    - Tracing Mode: Exploitation (velocity-based movement toward global best)

Reference:
    Chu, S. C., & Tsai, P. W. (2007). Computational intelligence based on 
    the behavior of cats. International Journal of Innovative Computing, 
    Information and Control, 3(1), 163-173.
"""

import numpy as np
from copy import deepcopy


class Cat:
    """
    Represents a single cat agent in the swarm.
    
    Attributes:
    -----------
    position : ndarray
        Current position in search space
    velocity : ndarray
        Current velocity vector
    fitness : float
        Fitness value at current position
    mode : str
        Current mode ('seeking' or 'tracing')
    best_position : ndarray
        Personal best position found
    best_fitness : float
        Personal best fitness value
    """
    
    def __init__(self, dim, bounds):
        """
        Initialize a cat with random position and velocity.
        
        Parameters:
        -----------
        dim : int
            Dimensionality of search space
        bounds : tuple
            (min, max) bounds for each dimension
        """
        self.dim = dim
        self.bounds = bounds
        
        # Random initialization within bounds
        self.position = np.random.uniform(bounds[0], bounds[1], dim)
        self.velocity = np.random.uniform(-1, 1, dim)
        
        self.fitness = float('inf')
        self.mode = 'seeking'  # Start in seeking mode
        
        # Personal best
        self.best_position = self.position.copy()
        self.best_fitness = float('inf')
    
    def clip_position(self):
        """Ensure position stays within bounds."""
        self.position = np.clip(self.position, self.bounds[0], self.bounds[1])
    
    def clip_velocity(self, v_max):
        """Limit velocity magnitude."""
        self.velocity = np.clip(self.velocity, -v_max, v_max)
    
    def update_personal_best(self):
        """Update personal best if current fitness is better."""
        if self.fitness < self.best_fitness:
            self.best_fitness = self.fitness
            self.best_position = self.position.copy()


class CatSwarmOptimizer:
    """
    Cat Swarm Optimization algorithm implementation.
    """
    
    def __init__(self, 
                 fitness_func,
                 dim=2,
                 n_cats=30,
                 max_iter=100,
                 MR=0.3,
                 SMP=5,
                 SRD=0.2,
                 CDC=0.8,
                 c1=2.0,
                 w=0.5,
                 bounds=(-5.12, 5.12)):
        """
        Initialize CSO optimizer.
        
        Parameters:
        -----------
        fitness_func : callable
            Objective function to minimize
        dim : int
            Dimensionality of search space
        n_cats : int
            Number of cats in swarm
        max_iter : int
            Maximum number of iterations
        MR : float
            Mixture Ratio (fraction of cats in tracing mode)
        SMP : int
            Seeking Memory Pool (number of copies in seeking mode)
        SRD : float
            Seeking Range of the selected Dimension (mutation range)
        CDC : float
            Counts of Dimension to Change (fraction of dimensions to mutate)
        c1 : float
            Acceleration constant for tracing mode
        w : float
            Inertia weight for velocity update
        bounds : tuple
            Search space bounds (min, max)
        """
        self.fitness_func = fitness_func
        self.dim = dim
        self.n_cats = n_cats
        self.max_iter = max_iter
        self.MR = MR
        self.SMP = SMP
        self.SRD = SRD
        self.CDC = CDC
        self.c1 = c1
        self.w = w
        self.bounds = bounds
        
        # Velocity bounds
        self.v_max = (bounds[1] - bounds[0]) * 0.2
        
        # Global best
        self.global_best_position = None
        self.global_best_fitness = float('inf')
        
        # Swarm
        self.cats = [Cat(dim, bounds) for _ in range(n_cats)]
        
        # History tracking
        self.history = {
            'global_best_fitness': [],
            'positions': [],
            'modes': [],
            'fitnesses': []
        }
        
        self.current_iteration = 0
    
    def evaluate_fitness(self):
        """Evaluate fitness for all cats."""
        for cat in self.cats:
            cat.fitness = self.fitness_func(cat.position)
            cat.update_personal_best()
            
            # Update global best
            if cat.fitness < self.global_best_fitness:
                self.global_best_fitness = cat.fitness
                self.global_best_position = cat.position.copy()
    
    def assign_modes(self):
        """Randomly assign cats to seeking or tracing mode based on MR."""
        n_tracing = int(self.n_cats * self.MR)
        
        # Randomly select cats for tracing mode
        tracing_indices = np.random.choice(self.n_cats, n_tracing, replace=False)
        
        for i, cat in enumerate(self.cats):
            if i in tracing_indices:
                cat.mode = 'tracing'
            else:
                cat.mode = 'seeking'
    
    def seeking_mode(self, cat):
        """
        Seeking mode: Create copies with mutations and select best.
        
        Process:
        1. Make SMP copies of the cat
        2. Randomly mutate CDC% of dimensions in each copy
        3. Evaluate all copies
        4. Select best copy (or use roulette wheel selection)
        """
        copies = []
        fitnesses = []
        
        for _ in range(self.SMP):
            # Create copy
            new_position = cat.position.copy()
            
            # Determine which dimensions to change
            n_dims_to_change = max(1, int(self.dim * self.CDC))
            dims_to_change = np.random.choice(self.dim, n_dims_to_change, replace=False)
            
            # Apply random perturbation
            for d in dims_to_change:
                mutation = np.random.uniform(-self.SRD, self.SRD)
                new_position[d] = cat.position[d] + mutation * (self.bounds[1] - self.bounds[0])
            
            # Clip to bounds
            new_position = np.clip(new_position, self.bounds[0], self.bounds[1])
            
            copies.append(new_position)
            fitnesses.append(self.fitness_func(new_position))
        
        # Select best copy (greedy selection)
        best_idx = np.argmin(fitnesses)
        cat.position = copies[best_idx]
        cat.fitness = fitnesses[best_idx]
    
    def tracing_mode(self, cat):
        """
        Tracing mode: Update velocity and position toward global best.
        
        Similar to PSO update:
        v = w*v + c1*r1*(global_best - position)
        position = position + v
        """
        # Random factor
        r1 = np.random.random(self.dim)
        
        # Update velocity
        cat.velocity = (self.w * cat.velocity + 
                       self.c1 * r1 * (self.global_best_position - cat.position))
        
        # Clip velocity
        cat.clip_velocity(self.v_max)
        
        # Update position
        cat.position = cat.position + cat.velocity
        cat.clip_position()
    
    def update_cats(self):
        """Update all cats based on their assigned mode."""
        for cat in self.cats:
            if cat.mode == 'seeking':
                self.seeking_mode(cat)
            else:  # tracing mode
                self.tracing_mode(cat)
    
    def record_history(self):
        """Record current state for visualization."""
        self.history['global_best_fitness'].append(self.global_best_fitness)
        self.history['positions'].append([cat.position.copy() for cat in self.cats])
        self.history['modes'].append([cat.mode for cat in self.cats])
        self.history['fitnesses'].append([cat.fitness for cat in self.cats])
    
    def optimize(self, verbose=True):
        """
        Run the CSO optimization algorithm.
        
        Parameters:
        -----------
        verbose : bool
            Print progress information
            
        Returns:
        --------
        dict
            Optimization results including best position, fitness, and history
        """
        # Initial evaluation
        self.evaluate_fitness()
        self.record_history()
        
        if verbose:
            print(f"Initial best fitness: {self.global_best_fitness:.6f}")
        
        # Main optimization loop
        for iteration in range(self.max_iter):
            self.current_iteration = iteration + 1
            
            # Assign modes
            self.assign_modes()
            
            # Update cat positions
            self.update_cats()
            
            # Evaluate fitness
            self.evaluate_fitness()
            
            # Record history
            self.record_history()
            
            if verbose and (iteration + 1) % 10 == 0:
                print(f"Iteration {iteration + 1}/{self.max_iter} | "
                      f"Best fitness: {self.global_best_fitness:.6f}")
        
        if verbose:
            print(f"\nOptimization complete!")
            print(f"Best position: {self.global_best_position}")
            print(f"Best fitness: {self.global_best_fitness:.6f}")
        
        return {
            'best_position': self.global_best_position,
            'best_fitness': self.global_best_fitness,
            'history': self.history,
            'iterations': self.max_iter
        }
    
    def get_current_state(self):
        """Get current state of all cats (for real-time visualization)."""
        return {
            'iteration': self.current_iteration,
            'positions': np.array([cat.position for cat in self.cats]),
            'modes': [cat.mode for cat in self.cats],
            'fitnesses': [cat.fitness for cat in self.cats],
            'global_best_position': self.global_best_position,
            'global_best_fitness': self.global_best_fitness
        }
