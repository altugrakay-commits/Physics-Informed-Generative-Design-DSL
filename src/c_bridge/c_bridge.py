# src/c_bridge/c_bridge.py
"""
ctypes bridge to the compiled C thermal kernel.

This module is deliberately small and dependency-free (except for NumPy).
If the shared library is missing, importing the module raises a clear
error early, so failures are obvious and isolated.
"""

import ctypes
import os
import platform
import numpy as np


def _library_filename() -> str:
    system = platform.system()
    if system == "Windows":
        return "thermal_core.dll"
    if system == "Darwin":
        return "thermal_core.dylib"
    return "thermal_core.so"


def _load_library() -> ctypes.CDLL:
    lib_path = os.path.join(os.path.dirname(__file__), _library_filename())
    if not os.path.exists(lib_path):
        raise FileNotFoundError(
            f"Compiled C library not found at {lib_path}. "
            "Compile thermal_core.c before running this module."
        )
    lib = ctypes.CDLL(lib_path)

    lib.thermal_step_2d.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.c_double,
        ctypes.c_double,
    ]
    lib.thermal_step_2d.restype = None
    return lib


_lib = _load_library()


def _ptr(arr: np.ndarray):
    """Returns a ctypes pointer to a contiguous float64 NumPy array."""
    return arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double))


def thermal_step(temp_in: np.ndarray,
                 alpha: np.ndarray,
                 dt: float,
                 dx: float) -> np.ndarray:
    """
    Executes one explicit thermal diffusion step in C.

    The boundary of the returned array equals the boundary of temp_in
    (fixed-temperature / Dirichlet boundary condition).
    """
    if temp_in.shape != alpha.shape:
        raise ValueError("temp_in and alpha must have identical shapes.")
    if temp_in.dtype != np.float64 or alpha.dtype != np.float64:
        raise TypeError("temp_in and alpha must be float64 arrays.")
    if not temp_in.flags["C_CONTIGUOUS"] or not alpha.flags["C_CONTIGUOUS"]:
        raise ValueError("Input arrays must be C-contiguous.")

    ny, nx = temp_in.shape
    temp_out = temp_in.copy()  # boundaries inherit temp_in values

    _lib.thermal_step_2d(
        _ptr(temp_in),
        _ptr(temp_out),
        _ptr(alpha),
        nx,
        ny,
        float(dt),
        float(dx),
    )
    return temp_out