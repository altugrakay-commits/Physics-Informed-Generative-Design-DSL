# src/physics/visualize.py
"""
Visualization module using PyVista.

This script runs a thermal simulation from the DSL and plots the
resulting temperature field as a 3D surface heatmap.
"""

import numpy as np
import pyvista as pv

from src.parser.parser import parse_dsl_string
from src.interpreter.interpreter import Interpreter


def visualize_thermal_interface():
    # 1. Define a test DSL interface
    dsl = '''
    interface "heat_test" {
        layers: [Si(5 nm), SiO2(10 nm)]
        thermal: transient_heat_flux(5e5 W/cm2)
    }
    '''

    # 2. Parse and Interpret
    print("Running thermal simulation...")
    model = parse_dsl_string(dsl)
    artifacts = Interpreter(model).execute()

    # 3. Extract the temperature array
    temp_2d = artifacts["heat_test"]["temperature"]
    print(f"Simulation complete. Shape: {temp_2d.shape}")

    # 4. Convert the 2D array to a PyVista grid
    # PyVista expects (X, Y, Z) coordinates. We create a flat plane (Z=0)
    ny, nx = temp_2d.shape
    x = np.arange(nx, dtype=float)
    y = np.arange(ny, dtype=float)
    x_grid, y_grid = np.meshgrid(x, y)
    z_grid = np.zeros_like(x_grid)  # Flat plane

    # Create a Structured Grid
    grid = pv.StructuredGrid(x_grid, y_grid, z_grid)
    
    # Attach the temperature data to the grid
    grid.point_data["Temperature (K)"] = temp_2d.flatten(order="F")

    # 5. Render the 3D plot
    plotter = pv.Plotter()
    
    # Add the mesh to the plotter, colored by temperature
    plotter.add_mesh(
        grid,
        scalars="Temperature (K)",
        cmap="inferno",         # 'inferno' is a great heatmap colormap
        show_edges=False,
        lighting=False,         # Turn off lighting so colors are flat and accurate
        clim=(300, 350)         # Fix the color scale between 300K and 350K
    )
    
    plotter.add_title("Transient Thermal Simulation (Final Timestep)")
    plotter.show_grid() # type: ignore
    
    # Open the interactive window
    plotter.show()


if __name__ == "__main__":
    visualize_thermal_interface()