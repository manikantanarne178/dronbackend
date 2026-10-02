#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=================================================="
echo "DroneVision / AutoDCR Backend Build Script"
echo "=================================================="

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Verify COLMAP availability if present on host
if command -v colmap &> /dev/null; then
    echo "COLMAP is installed at: $(which colmap)"
    colmap -h | head -n 1 || true
else
    echo "COLMAP binary not in PATH. Direct Python SfM Engine (Open3D + OpenCV) will be used."
fi

echo "Build completed successfully."
