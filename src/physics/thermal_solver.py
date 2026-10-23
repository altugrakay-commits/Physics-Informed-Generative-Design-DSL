# src/physics/thermal_solver.py
"""
Transient thermal solver for material interfaces.

This module is the driver for the C thermal kernel exposed via
c_bridge. It sets up a uniform 2D grid representing a cross-section
of the interface stack, initializes the temperature field, applies
the interface's heat flux as a source term, and iterates the C
finite-difference kernel forward in time.

The solver is intentionally minimal: it treats the interface as a
homogeneous slab with a single effective thermal diffusivity. A more
physically faithful implementation would assign per-layer diffusivity
and solve the Stefan problem at each material boundary. That is a
roadmap item, not a current capability.
"""

import numpy as np

from src.c_bridge.c_bridge import thermal_step


# Default grid resolution. High enough to see structure, low enough
# that a full transient run completes in well under a second.
_GRID_NY = 64
_GRID_NX = 64

# Default number of time steps per simulation.
_NUM_STEPS = 200

# Effective thermal diffusivity used when no material database is
# available. This value (1e-5 m^2/s) is representative of a
# metal-oxide interface at room temperature.
_DEFAULT_ALPHA = 1e-5

# Spatial step size in metres. Corresponds roughly to the grid
# resolution spanning a 1 mm x 1 mm cross-section.
_DEFAULT_DX = 1.0e-3 / _GRID_NX

def _parse_heat_flux(thermal_block):

    """
    Convert the DSL's heat-flux value into SI units (W/m^2).

    The DSL specifies flux in either W/cm^2 or W/m^2. This function
    returns the value in W/m^2 regardless of the original unit.
    """

    flux = thermal_block.flux
    unit = thermal_block.unit

    if unit == "W/cm2":
        # 1 cm^2 = 1e-4 m^2, so W/cm^2 = W / 1e-4 m^2 = 1e4 W/m^2
        return flux * 1.0e4
    if unit == "W/m2":
        return flux

    raise ValueError(f"Unsupported heat-flux unit: {unit}")

def solve_thermal_transient(interface):

    """
    Run a transient thermal simulation for a parsed Interface.

    Args:
        interface: A textX Interface object with a .thermal block.

    Returns:
        A dictionary containing:
          - name:          the interface name
          - temperature:   the final 2D temperature field (ny x nx)
          - time_steps:    number of iterations performed
          - flux_si:       applied heat flux in W/m^2
          - peak_temp:     maximum temperature reached in K
    """

    if not hasattr(interface, "thermal") or interface.thermal is None:
        raise ValueError(
            f"Interface '{interface.name}' has no thermal block; "
            "cannot run thermal simulation"
        )

    # Physical parameters from the DSL.
    flux_si = _parse_heat_flux(interface.thermal)

    # Grid and material parameters.
    ny, nx = _GRID_NY, _GRID_NX
    dx = _DEFAULT_DX
    alpha_value = _DEFAULT_ALPHA

    # CFL stability condition for explicit 2D diffusion:
    #     dt <= dx^2 / (4 * alpha)
    # We take 90% of the limit to stay safely inside the stable region.
    dt = 0.9 * (dx * dx) / (4.0 * alpha_value)

    # Initialize the temperature field. The whole domain starts at
    # 300 K (roughly room temperature). The bottom edge is held at
    # 300 K throughout the simulation, acting as a heat sink.
    temp = np.full((ny, nx), 300.0, dtype=np.float64)

    # Apply the heat flux as a temperature source at the top edge.
    # The conversion from flux (W/m^2) to a temperature increment
    # uses a simplified lumped model: dT = flux * dt / (rho * cp * dx),
    # with rho and cp folded into a single effective coefficient.
    # For a proper treatment, we would solve the heat equation with
    # a Neumann boundary condition on the top face.
    effective_rho_cp = 1.0e6    # J / (m^3 K), placeholder
    dT_top = flux_si * dt / (effective_rho_cp * dx)
    temp[0,:] += dT_top

    # Diffusivity field: uniform for now.
    alpha = np.full((ny,nx), alpha_value, dtype=np.float64)

    # Iterate the C kernel. Each call advances the field one dt.
    for _ in range(_NUM_STEPS):
        temp = thermal_step(temp, alpha, dt, dx)

    return {
        "name": interface.name,
        "temperature": temp,
        "time_steps": _NUM_STEPS,
        "flux_si": flux_si,
        "peak_temp": float(np.max(temp))
    }