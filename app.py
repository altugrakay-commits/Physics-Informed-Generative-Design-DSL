# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import platform
import subprocess

os.makedirs("output", exist_ok=True)


if platform.system() == "Linux":
    so_path = "src/c_bridge/thermal_core.so"
    if not os.path.exists(so_path):
        print("Compiling C kernel for Linux cloud environment...")
        subprocess.run([
            "gcc", "-O3", "-shared", "-fPIC", "-o", so_path, 
            "src/c_bridge/thermal_core.c"
        ], check=True)

from src.interpreter.interpreter import Interpreter
from src.parser.parser import parse_dsl_string

# Page config
st.set_page_config(page_title="Physics DSL Engine", layout="wide")

st.title("⚙️ Physics-Informed Generative Design DSL")
st.markdown("Write DSL code below to generate 3D CAD models and run transient thermal simulations.")

# Layout: 2 columns (Left = Input, Right = Output)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("DSL Input")
    default_dsl = '''part "heat_sink_base" {
    geometry: box(50, 30, 5)
    material: aluminum
}

interface "gate_stack" {
    layers: [MoS2(5 nm), Al2O3(10 nm)]
    thermal: transient_heat_flux(5e5 W/cm2)
}'''
    
    dsl_input = st.text_area("Edit your DSL:", value=default_dsl, height=300)
    
    run_button = st.button("🚀 Run Compiler & Solver", use_container_width=True)

with col2:
    st.subheader("Generated Artifacts")
    
    if run_button:
        with st.spinner("Parsing and executing DSL..."):
            try:
                # 1. Parse and Interpret
                model = parse_dsl_string(dsl_input)
                artifacts = Interpreter(model).execute()
                
                # 2. Display CAD Outputs
                # 2. Display CAD Outputs
                st.write("### 3D Geometry Files")
                for name, data in artifacts.items():
                    if "stl_path" in data:
                        st.success(f"Generated **{data['type']}** for '{name}'")
                        
                        # Read the STL file as bytes for the download button
                        with open(data['stl_path'], "rb") as file:
                            stl_data = file.read()
                            
                        st.download_button(
                            label=f"📥 Download {name}.stl",
                            data=stl_data,
                            file_name=f"{name}.stl",
                            mime="application/octet-stream",
                            key=f"dl_{name}"
                        )
                
                # 3. Display Thermal Simulation Outputs
                st.write("### Thermal Simulation")
                thermal_found = False
                for name, data in artifacts.items():
                    if "temperature" in data:
                        thermal_found = True
                        
                        st.write(f"**Interface:** {name}")
                        st.write(f"**Peak Temperature:** {data['peak_temp']:.2f} K")
                        
                        # Use Matplotlib to render the 2D array for Streamlit
                        fig, ax = plt.subplots(figsize=(6, 4))
                        im = ax.imshow(data['temperature'], cmap='inferno', origin='upper', extent=[0, 64, 64, 0])
                        ax.set_title("Temperature Distribution (K)")
                        ax.set_xlabel("X Grid")
                        ax.set_ylabel("Y Grid")
                        fig.colorbar(im, ax=ax, label="Temperature (K)")
                        
                        st.pyplot(fig)
                
                if not thermal_found:
                    st.info("No interfaces with a `thermal` block were found.")

            except Exception as e:
                st.error(f"Compilation Error: {e}")