# 🐱 CSO Visual Simulator

**Cat Swarm Optimization (CSO) Algorithm Visualization on the Rastrigin Function**

An interactive Python-based simulator that demonstrates the Cat Swarm Optimization algorithm in action — visually and computationally. Watch as cats explore and exploit the Rastrigin function landscape to find the global minimum!

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Algorithm Details](#algorithm-details)
- [Project Structure](#project-structure)
- [Parameters Guide](#parameters-guide)
- [Screenshots](#screenshots)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## 🎯 Overview

This project implements a complete **Cat Swarm Optimization (CSO)** simulator with real-time visualization. CSO is a population-based metaheuristic algorithm inspired by cat behavior, featuring two distinct modes:

- **🔵 Seeking Mode**: Cats explore their local neighborhood (exploration)
- **🔴 Tracing Mode**: Cats chase the global best position (exploitation)

The simulator applies CSO to minimize the **Rastrigin function**, a challenging multimodal benchmark function with many local minima.

---

## ✨ Features

- ✅ **Complete CSO Implementation**: Fully functional seeking & tracing modes
- ✅ **Real-time Visualization**: Watch cats move on the Rastrigin landscape
- ✅ **Interactive Web Interface**: Adjust parameters via a user-friendly dashboard
- ✅ **Color-coded Behavior**: Distinguish seeking (blue) vs tracing (red) cats
- ✅ **Convergence Analysis**: Plot fitness improvement over iterations
- ✅ **Frame-by-frame Playback**: Review simulation with play/pause controls
- ✅ **Educational Clarity**: Perfect for learning optimization algorithms

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step-by-Step Setup

1. **Clone or download this repository**

```bash
cd c:\projects\cso
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

The required packages are:
- `flask` - Web framework
- `numpy` - Numerical computations
- `matplotlib` - Visualization

---

## 🎮 Usage

### Running the Application

1. **Start the Flask server**

```bash
python app.py
```

2. **Open your browser**

Navigate to: **http://localhost:5000**

3. **Configure parameters** (or use defaults)

   - Number of cats: 30
   - Max iterations: 30
   - Mixture Ratio (MR): 0.3
   - Other CSO parameters...

4. **Click "Start Simulation"**

5. **Watch the magic happen!** 🎬

   - Cats will explore the Rastrigin landscape
   - Blue circles = seeking mode (exploration)
   - Red triangles = tracing mode (exploitation)
   - Gold star = current best position

6. **Review results**

   - Use playback controls to step through frames
   - View convergence curve
   - Check final fitness and position

---

## 🧮 Algorithm Details

### Cat Swarm Optimization (CSO)

CSO alternates each cat between two behavioral modes:

#### Seeking Mode (Exploration)
```
1. Create SMP copies of the cat
2. Mutate CDC% of dimensions in each copy
3. Evaluate fitness of all copies
4. Select the best copy
```

#### Tracing Mode (Exploitation)
```
1. Update velocity toward global best (PSO-style)
   v = w*v + c1*r*(global_best - position)
2. Update position
   position = position + v
3. Clip to bounds
```

### Rastrigin Function

The Rastrigin function is defined as:

```
f(x, y) = 20 + x² - 10cos(2πx) + y² - 10cos(2πy)
```

**Properties:**
- Global minimum: f(0, 0) = 0
- Domain: [-5.12, 5.12]
- Highly multimodal (many local minima)
- Excellent for testing optimization algorithms

---

## 📁 Project Structure

```
c:\projects\cso\
│
├── app.py                 # Flask web application
├── cso.py                 # Cat Swarm Optimization algorithm
├── rastrigin.py           # Rastrigin function implementation
├── visualizer.py          # Visualization engine
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── templates/
│   └── index.html        # Main web interface
│
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    ├── js/
    │   └── main.js       # Frontend JavaScript
    └── frames/           # Generated visualization frames
```

---

## ⚙️ Parameters Guide

### Population Settings

| Parameter    | Description              | Range   | Default |
|--------------|--------------------------|---------|---------|
| `n_cats`     | Number of cats (agents)  | 10-100  | 30      |
| `max_iter`   | Maximum iterations       | 10-200  | 50      |

### CSO Algorithm Settings

| Parameter | Description                           | Range    | Default |
|-----------|---------------------------------------|----------|---------|
| `MR`      | Mixture Ratio (% in tracing mode)     | 0.1-0.9  | 0.3     |
| `SMP`     | Seeking Memory Pool (copies)          | 2-10     | 5       |
| `SRD`     | Seeking Range (mutation magnitude)    | 0.05-0.5 | 0.2     |
| `CDC`     | Counts of Dimension to Change         | 0.1-1.0  | 0.8     |

### Velocity Settings (Tracing Mode)

| Parameter | Description                    | Range   | Default |
|-----------|--------------------------------|---------|---------|
| `c1`      | Acceleration constant          | 0.5-4.0 | 2.0     |
| `w`       | Inertia weight                 | 0.1-1.0 | 0.5     |

---

## 🎨 Screenshots

### Main Interface
- Left panel: Parameter controls
- Right panel: Live visualization
- Bottom: Convergence curve

### Visualization Legend
- 🔵 **Blue circles** = Seeking mode cats (exploring)
- 🔴 **Red triangles** = Tracing mode cats (exploiting)
- ⭐ **Gold star** = Global best position
- ❌ **Green X** = True optimum (0, 0)

---

## 🔮 Future Enhancements

Potential improvements and extensions:

- [ ] Add more benchmark functions (Sphere, Rosenbrock, Ackley)
- [ ] Real-time animation (WebSocket streaming)
- [ ] 3D visualization option
- [ ] Parameter auto-tuning
- [ ] Comparison with other algorithms (PSO, GA, ACO)
- [ ] Export results to CSV/JSON
- [ ] Mobile-responsive design
- [ ] Multi-run statistical analysis

---

## 📚 References

**Original CSO Paper:**
> Chu, S. C., & Tsai, P. W. (2007). Computational intelligence based on the behavior of cats. *International Journal of Innovative Computing, Information and Control*, 3(1), 163-173.

**Rastrigin Function:**
> Rastrigin, L. A. (1974). Systems of extremal control. *Nauka*.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

---

## 📄 License

This project is open source and available for educational purposes.

---

## 🎓 Educational Use

This simulator is designed for:

- **Students** learning optimization algorithms
- **Researchers** experimenting with metaheuristics
- **Educators** demonstrating swarm intelligence
- **Developers** understanding CSO implementation

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'flask'`
- **Solution**: Run `pip install -r requirements.txt`

**Issue**: Port 5000 already in use
- **Solution**: Change port in `app.py`: `app.run(..., port=5001)`

**Issue**: Matplotlib backend errors
- **Solution**: The code uses `Agg` backend (non-GUI), should work on all systems

**Issue**: Frames not displaying
- **Solution**: Check `static/frames/` directory permissions

---

## 💡 Tips for Best Results

1. **Start with default parameters** to see typical behavior
2. **Increase iterations (100-200)** for better convergence
3. **Higher MR (0.5-0.7)** = more exploitation, faster convergence
4. **Lower MR (0.2-0.3)** = more exploration, avoid local minima
5. **More cats (50-100)** = better exploration but slower computation
6. **Watch the seeking cats** explore randomly vs **tracing cats** move toward the star

---

## 🌟 Enjoy Exploring!

Watch the cats find the minimum of the Rastrigin function — it's mesmerizing! 🐱✨

For questions or feedback, feel free to open an issue or reach out.

**Happy Optimizing!** 🚀
