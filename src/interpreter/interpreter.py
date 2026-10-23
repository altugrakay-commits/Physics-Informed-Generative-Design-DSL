# src/interpreter/interpreter.py
"""
The interpreter walks a parsed DSL model and dispatches each
declarative statement to the appropriate backend.

There are two kinds of statements in the current language:

  * Part       -- a mechanical component with geometry and constraints.
                  Routed to the CAD generator.

  * Interface  -- a material stack with optional physics and thermal
                  blocks. Routed to the thermal solver (and eventually
                  to the Poisson-Schrodinger solver).

The interpreter's job is dispatch, not computation. It never inspects
what kind of object a backend returns; it only collects the results
into a dictionary keyed by the declaration's name.
"""

from src.cad.cad_generator import generate_cad_model
from src.physics.thermal_solver import solve_thermal_transient

class Interpreter:
    """
    Walks a parsed Model and produces a dictionary of artifacts.

    Usage:
        model = parse_dsl("examples/heat_sink.dsl")
        artifacts = Interpreter(model).execute()
    """

    def __init__(self, model):
        self.model = model
        self.artifacts = {}

    def execute(self):
        """
        Interpret the model. Returns the artifacts dictionary.
        """
        for part in self.model.parts:
            self._handle_part(part)

        for interface in self.model.interfaces:
            self._handle_interface(interface)

        return self.artifacts
    
    # -----------------------------------------------------------------
    # Dispatch handlers
    # -----------------------------------------------------------------

    def _handle_part(self, part):
        """
        A Part is routed to the CAD generator. The result is stored
        under the part's name.
        """
        artifact = generate_cad_model(part)
        self.artifacts[part.name] = artifact

    def _handle_interface(self, interface):
        """
        An Interface may or may not have a thermal block. If it does,
        we run the thermal solver. Otherwise we record a bare
        descriptor so every declared entity produces exactly one
        artifact.
        """
        has_thermal = (
            hasattr(interface, "thermal")
            and interface.thermal is not None
        )

        if has_thermal:
            artifact = solve_thermal_transient(interface)
        else:
            artifact = {
                "name": interface.name,
                "type": "interface",
                "layers": [
                    {"material": layer.material, "thickness": layer.thickness, "unit": layer.unit}
                    for layer in interface.layers
                ]
            }

        self.artifacts[interface.name] = artifact

# ---------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------
def interpret_file(dsl_path):
    """
    Parse a DSL file and interpret it in one step.

    Returns the artifacts dictionary, or None if the file failed
    to parse.
    """
    # Import here to avoid a circular import at module load time.
    from src.parser.parser import parse_dsl

    model = parse_dsl(dsl_path)
    if model is None:
        return None

    return Interpreter(model).execute()