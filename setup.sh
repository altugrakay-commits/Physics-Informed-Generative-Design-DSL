#!/bin/bash

# Compile the C kernel for Linux if the .so file doesn't exist
if [ ! -f "src/c_bridge/thermal_core.so" ]; then
    echo "Compiling C kernel for Linux..."
    gcc -O3 -shared -fPIC -o src/c_bridge/thermal_core.so src/c_bridge/thermal_core.c
fi