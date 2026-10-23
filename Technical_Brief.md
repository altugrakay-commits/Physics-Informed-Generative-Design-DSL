# Technical Brief: Physics-Informed Generative Design DSL

This document outlines the software architecture, numerical methods, and foreign function interface (FFI) implementation of the DSL engine.

## 1. The Language Layer (Parser & Interpreter)
The domain-specific language is defined using **textX**, a meta-language for building parsers. The grammar (`physics_dsl.tx`) defines the syntax for mechanical parts (`box`, `cylinder`), materials, and multi-layer interfaces. 

* **Lexing/Parsing:** textX generates a parser that converts raw DSL text into a structured Python object graph (Abstract Syntax Tree).
* **Interpreting:** The `Interpreter` class walks this object graph. It acts as a router, dispatching `Part` objects to the CAD engine and `Interface` objects to the physics engine, decoupling the language syntax from the execution logic.

## 2. The CAD Layer (Generative Geometry)
Parsed geometry is passed to **CadQuery**, a Python-based parametric CAD scripting framework.
* The engine maps DSL primitives (e.g., `box(50, 30, 5)`) to CadQuery `Workplane` operations.
* It exports industry-standard `.step` (B-Rep geometry) and `.stl` (triangular mesh) files.

## 3. The Performance Layer (C Bridge & ctypes)
Python is too slow for iterative finite-difference inner loops. Therefore, the thermal diffusion kernel is written in **C** and bridged to Python using the standard library's `ctypes` module.

### The C Kernel (`thermal_core.c`)
The kernel executes a 5-point finite-difference stencil for a 2D uniform grid:
`T_new[i,j] = T[i,j] + (alpha * dt / dx^2) * (T[i-1,j] + T[i+1,j] + T[i,j-1] + T[i,j+1] - 4*T[i,j])`

### The Strict FFI Contract
Bridging Python and C requires strict memory management:
1. **Type Safety:** `ctypes.argtypes` explicitly defines the C function signature to prevent pointer corruption.
2. **Memory Layout:** The C kernel assumes row-major, C-contiguous arrays. The Python wrapper enforces `temp_in.flags["C_CONTIGUOUS"]` before passing NumPy arrays to C.
3. **Boundary Conditions:** The C kernel only updates interior nodes. The Python wrapper pre-fills the boundary nodes with the input array's values (`temp_in.copy()`), enforcing a strict fixed-temperature (Dirichlet) boundary condition.

## 4. Numerical Stability (The CFL Condition)
Explicit finite-difference schemes for parabolic PDEs (like the heat equation) are conditionally stable. The solver calculates the time step dynamically to satisfy the Courant-Friedrichs-Lewy (CFL) condition:
`dt <= dx^2 / (4 * alpha)`
The solver uses 90% of this maximum allowable time step to ensure numerical stability without sacrificing performance.

## 5. Visualization
* **Physics:** The resulting temperature field (NumPy array) is visualized using **PyVista** (3D surface mapping) and **Matplotlib** (2D heatmaps in Streamlit).
* **UI:** **Streamlit** provides the web interface, allowing users to write DSL code, execute the compiler pipeline, and download generated geometry files.