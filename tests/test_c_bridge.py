# tests/test_c_bridge.py
"""
Unit tests for the C bridge.

Verifies that the compiled C kernel produces the same results as a
pure NumPy reference implementation.
"""

import time

import numpy as np
import pytest

from src.c_bridge.c_bridge import thermal_step


def _numpy_reference(temp_in, alpha, dt, dx):
    """Pure NumPy implementation used to validate the C kernel."""
    temp_out = temp_in.copy()
    inv_dx2 = 1.0 / (dx * dx)
    interior = temp_in[1:-1, 1:-1]
    laplacian = (
        temp_in[1:-1, :-2] + temp_in[1:-1, 2:]
        + temp_in[:-2, 1:-1] + temp_in[2:, 1:-1]
        - 4.0 * interior
    ) * inv_dx2
    temp_out[1:-1, 1:-1] = interior + dt * alpha[1:-1, 1:-1] * laplacian
    return temp_out


def test_c_matches_numpy_reference():
    ny, nx = 64, 64
    rng = np.random.default_rng(seed=42)

    temp_in = rng.random((ny, nx)) * 300.0
    alpha = np.full((ny, nx), 1e-4, dtype=np.float64)
    dt = 1e-3
    dx = 1e-3

    out_c = thermal_step(temp_in, alpha, dt, dx)
    out_py = _numpy_reference(temp_in, alpha, dt, dx)

    np.testing.assert_allclose(out_c, out_py, rtol=1e-12, atol=1e-12)


def test_boundary_preserved():
    """Boundary values must be identical between input and output."""
    ny, nx = 16, 16
    temp_in = np.random.rand(ny, nx).astype(np.float64) * 300.0
    alpha = np.full((ny, nx), 1e-4, dtype=np.float64)
    out = thermal_step(temp_in, alpha, dt=1e-4, dx=1e-4)

    np.testing.assert_array_equal(out[0, :], temp_in[0, :])
    np.testing.assert_array_equal(out[-1, :], temp_in[-1, :])
    np.testing.assert_array_equal(out[:, 0], temp_in[:, 0])
    np.testing.assert_array_equal(out[:, -1], temp_in[:, -1])


def test_shapes_preserved():
    ny, nx = 32, 48
    temp_in = np.zeros((ny, nx), dtype=np.float64)
    alpha = np.ones((ny, nx), dtype=np.float64)
    out = thermal_step(temp_in, alpha, dt=1e-3, dx=1e-3)
    assert out.shape == (ny, nx)


def test_mismatched_shapes_raises():
    temp_in = np.zeros((10, 10), dtype=np.float64)
    alpha = np.zeros((5, 5), dtype=np.float64)
    with pytest.raises(ValueError):
        thermal_step(temp_in, alpha, dt=1e-3, dx=1e-3)


def test_performance_sanity():
    """Quick sanity check that the C kernel is not pathologically slow."""
    ny, nx = 512, 512
    temp_in = np.random.rand(ny, nx).astype(np.float64) * 300.0
    alpha = np.full((ny, nx), 1e-4, dtype=np.float64)

    t0 = time.perf_counter()
    for _ in range(10):
        thermal_step(temp_in, alpha, dt=1e-4, dx=1e-4)
    elapsed = time.perf_counter() - t0

    assert elapsed < 2.0, f"C kernel too slow: {elapsed:.3f}s for 10 steps"