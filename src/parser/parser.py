"""
Parser for the Physics-Informed Generative Design DSL.

Loads the textX grammar and converts a .dsl fiel into a Python object 
graph. This module has no dependencies on CAD or physics libraries, 
which keeps it fast and easily testable.
"""

from textx import metamodel_from_file
from textx.exceptions import TextXSyntaxError
import os

def get_metamodel():
    """Loads and returns the textX meta-model from the grammar file."""
    grammar_path = os.path.join(os.path.dirname(__file__), "..", "grammar", "physics_dsl.tx")
    grammar_path = os.path.abspath(grammar_path)
    return metamodel_from_file(grammar_path)

def parse_dsl(file_path: str):
    """
    Parses a DSL file and returns the model object.
    
    Args:
        file_path: Path to the .dsl source file.
        
    Returns:
        The parsed textX model, or None on syntax error
    """
    mm = get_metamodel()
    try:
        model = mm.model_from_file(file_path)
        return model
    except TextXSyntaxError as e:
        print(f"[Parser] Syntax error in {file_path}: {e}")
    except FileNotFoundError:
        print(f"[Parser] File not found: {file_path}")
        return None

def parse_dsl_string(dsl_text: str):
    """Parses a DSL string. Useful for tests."""
    mm = get_metamodel()
    return mm.model_from_str(dsl_text)