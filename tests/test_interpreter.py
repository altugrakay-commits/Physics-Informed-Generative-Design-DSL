# tests/test_interpreter.py
"""
Unit tests for the interpreter.

These tests exercise the dispatch logic: given a parsed Model,
does the interpreter route each entity to the right backend and
collect the results correctly?

Because the thermal solver calls into the C bridge, the interface
tests here also serve as integration tests: they confirm that
parser -> interpreter -> physics -> C kernel works end-to-end.
"""

import numpy as np
import pytest
import os

from src.interpreter.interpreter import Interpreter, interpret_file
from src.parser.parser import parse_dsl_string

# ---------------------------------------------------------------------
# Parts -> CAD stub
# ---------------------------------------------------------------------

def test_interpret_simple_part():
    """A single Part produces exactly one artifact, keyed by name."""
    dsl = '''
    part "bracket" {
    geometry: box(10,20,3)
    material: steel}
    '''
    model = parse_dsl_string(dsl)
    artifacts = Interpreter(model).execute()

    assert len(artifacts) == 1
    assert "bracket" in artifacts

    bracket = artifacts["bracket"]
    assert bracket["name"] == "bracket"
    assert bracket["type"] == "box"
    assert bracket["material"] == "steel"
    
    # Checks the file paths instead of width/height dictionaries.
    assert os.path.exists(bracket["stl_path"])
    assert bracket["solid"] is not None

def test_interpret_cylinder_part():
    """The interpreter routes Cylinder geometry correctly."""
    dsl = '''
    part "pin" {geometry: cylinder(2,10) material: copper}
    '''
    model = parse_dsl_string(dsl)
    artifacts = Interpreter(model).execute()

    pin = artifacts["pin"]
    assert pin["type"] == "cylinder"
    assert pin["material"] == "copper"
    
    assert os.path.exists(pin["stl_path"])
    assert pin["solid"] is not None

def test_multiple_parts():
    """Two Parts produce two artifacts, each keyed by its own name."""
    dsl = '''
    part "base" {geometry: box(50,30,5) material: aluminium}
    part "pin" {geometry: cylinder(2,10) material: copper}
    '''
    model = parse_dsl_string(dsl)
    artifacts = Interpreter(model).execute()

    assert set(artifacts.keys()) == {"base","pin"}
    assert artifacts["base"]["type"] == "box"
    assert artifacts["pin"]["type"] == "cylinder"

# ---------------------------------------------------------------------
# Interfaces -> thermal solver (which calls the C bridge)
# ---------------------------------------------------------------------

def test_interpret_interface_with_thermal():
    """An Interface with a thermal block runs the solver."""
    dsl = '''
    interface "gate_stack" {layers: [MoS2 (5 nm), Al2O3 (10 nm)] thermal: transient_heat_flux(1e6 W/cm2)}
    '''
    model = parse_dsl_string(dsl)
    artifacts = Interpreter(model).execute()

    assert "gate_stack" in artifacts
    result = artifacts["gate_stack"]

    # The thermal solver returns these keys.
    assert result["name"] == "gate_stack"
    assert result["time_steps"] > 0
    assert result["flux_si"] == pytest.approx(1e6 * 1e4)

    # The temperature field is a 2D NumPy array.
    temp = result["temperature"]
    assert isinstance(temp, np.ndarray)
    assert temp.ndim == 2

    # No numerical blow-up should have occurred.
    assert np.isfinite(temp).all()
    assert result["peak_temp"] > 300.0

def test_interpret_interface_without_thermal():
    """An Interface with no thermal block yield a bare descriptor."""
    dsl = '''
    interface "gate_stack" {layers: [Ti(2 nm), Au(50 nm)]}
    '''
    model = parse_dsl_string(dsl)
    artifacts = Interpreter(model).execute()

    descriptor = artifacts["gate_stack"]
    assert descriptor["type"] == "interface"
    assert len(descriptor["layers"]) == 2
    assert descriptor["layers"][0]["material"] == "Ti"
    assert descriptor["layers"][0]["thickness"] == 2
    assert descriptor["layers"][1]["material"] == "Au"

# ---------------------------------------------------------------------
# Combined model
# ---------------------------------------------------------------------

def test_interpret_mixed_model():
    """Parts and Interfaces coexist in one artifact dictionary."""
    dsl = '''
    part "heat_sink" {geometry: box(50, 30, 5) material: aluminum}
    interface "gate_stack" {layers: [MoS2(5 nm), Al2O3(10 nm)] thermal: transient_heat_flux(1e6 W/cm2)}
    '''
    model = parse_dsl_string(dsl)
    artifacts = Interpreter(model).execute()

    assert set(artifacts.keys()) == {"heat_sink","gate_stack"}
    assert artifacts["heat_sink"]["type"] == "box"
    assert "temperature" in artifacts["gate_stack"]

# ---------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------

def test_interpret_file_example():
    """The convenience function parses and interprets in one call."""
    import os

    example_path = os.path.join(
        os.path.dirname(__file__), "..", "examples", "heat_sink.dsl"
    )
    artifacts = interpret_file(example_path)

    assert artifacts is not None
    assert "heat_sink_base" in artifacts
    assert "mounting_pin" in artifacts
    assert "MoS2_Al2O3_gate" in artifacts

    assert artifacts["heat_sink_base"]["type"] == "box"
    assert artifacts["mounting_pin"]["type"] == "cylinder"
    assert "temperature" in artifacts["MoS2_Al2O3_gate"]

def test_interpret_file_missing_returns_none():
    """Interpret_file returns None when the file cannot be parsed."""
    artifacts = interpret_file("this/path/does/not/exist.dsl")
    assert artifacts is None

# ---------------------------------------------------------------------
# Return contract
# ---------------------------------------------------------------------

def test_execute_returns_dict():
    """The execute method always returns a dictionary."""
    dsl = 'part "solo" {geometry: box(1,1,1)}'
    model = parse_dsl_string(dsl)
    result = Interpreter(model).execute()
    assert isinstance(result, dict)