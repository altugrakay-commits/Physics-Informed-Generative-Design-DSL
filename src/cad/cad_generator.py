import os
import cadquery as cq

def generate_cad_model(part):
    # Create the output directory EVERY time a model is generated
    _OUTPUT_DIR = os.path.join(os.getcwd(), "output")
    os.makedirs(_OUTPUT_DIR, exist_ok=True)

    geo = part.geometry

    if geo is None:
        return {"name": part.name, "type": "unspecified", "solid": None}

    geo_type = geo.__class__.__name__
    wp = cq.Workplane("XY")

    if geo_type == "Box":
        solid = wp.box(geo.width, geo.height, geo.depth)
        file_prefix = f"{part.name}_box"
    elif geo_type == "Cylinder":
        solid = wp.circle(geo.radius).extrude(geo.height)
        file_prefix = f"{part.name}_cylinder"
    else:
        raise ValueError(f"Unknown geometry type: {geo_type}")

    step_path = os.path.join(_OUTPUT_DIR, f"{file_prefix}.step")
    stl_path = os.path.join(_OUTPUT_DIR, f"{file_prefix}.stl")

    cq.exporters.export(solid, step_path)
    cq.exporters.export(solid, stl_path)

    return {
        "name": part.name,
        "type": geo_type.lower(),
        "material": part.material,
        "solid": solid,
        "step_path": step_path,
        "stl_path": stl_path,
    }