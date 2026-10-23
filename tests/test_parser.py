# Test suite: the first piece of evidence for the judges that the language works.

"""
Unit tests for the DSL parser.

These tests prove that the raw text is correctly converted into a structured 
Python object graph, independent of any CAD or physics backend.
"""

import os
import pytest
from textx import TextXSyntaxError
from src.parser.parser import parse_dsl, parse_dsl_string

def test_parse_simple_part():
    dsl = '''
    part "bracket" {
        geometry: box(10, 20, 3)
        material: steel
        constraint stress {max_von_mises < 250 MPa}
    }
    '''
    model = parse_dsl_string(dsl)
    assert model is not None
    assert len(model.parts) == 1
    part = model.parts[0]
    assert part.name == "bracket"
    assert part.material == "steel"
    assert part.geometry.width == 10
    assert part.geometry.height == 20
    assert part.geometry.depth == 3
    assert part.constraint.max_stress == 250
    assert part.constraint.unit == "MPa"

def test_parse_cylinder():
    dsl = '''
    part "pin" {
        geometry: cylinder(2,10)
        }
        '''
    model = parse_dsl_string(dsl)
    assert model.parts[0].geometry.__class__.__name__ == "Cylinder"
    assert model.parts[0].geometry.radius == 2
    assert model.parts[0].geometry.height == 10

def test_parse_interface():
    dsl = '''
    interface "gate_stack" {
        layers: [MoS2(5 nm), Al2O3(10 nm)]
        physics: coupled_poisson_schrodinger
        thermal: transient_heat_flux(1e6 W/cm2)
        }
        '''
    model = parse_dsl_string(dsl)
    assert len(model.interfaces) == 1
    iface = model.interfaces[0]
    assert iface.name == "gate_stack"
    assert len(iface.layers) == 2
    assert iface.layers[0].material == "MoS2"
    assert iface.layers[0].thickness == 5
    assert iface.layers[0].unit == "nm"
    assert iface.thermal.flux == 1e6
    assert iface.thermal.unit == "W/cm2"

def test_parse_example_file():
    """Parses the bundled example and checks the overall structure."""
    example_path = os.path.join(
        os.path.dirname(__file__), "..", "examples", "heat_sink.dsl"
    )
    model = parse_dsl(example_path)
    assert model is not None
    assert len(model.parts) == 2
    assert len(model.interfaces) == 1
    assert model.parts[0].name == "heat_sink_base"
    assert model.interfaces[0].name == "MoS2_Al2O3_gate"

def test_malformed_dsl_raises():
    """Malformed DSL raises TextXSyntaxError when parsed from string."""
    bad_dsl = 'part "broken" {geometry: box(1,2) '  # Missing braces/closing
    with pytest.raises(TextXSyntaxError):
        parse_dsl_string(bad_dsl)

def test_missing_file_returns_none():
    """The file-based parser returns None for a missing file rather than raising."""
    model = parse_dsl("this/path/does/not/exist.dsl")
    assert model is None