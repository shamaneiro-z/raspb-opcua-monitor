#!/bin/bash
# Build Python wheels for offline deployment on Raspberry Pi
# Run this once on a machine with internet, then copy wheels/ to the Pi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
WHEELS_DIR="$REPO_ROOT/collector/wheels"

echo "Building wheels for offline deployment..."
mkdir -p "$WHEELS_DIR"

# Install wheel build tools
pip install --upgrade pip wheel setuptools

# Build wheels from requirements.txt
pip wheel --wheel-dir "$WHEELS_DIR" -r "$REPO_ROOT/collector/requirements.txt"

echo "✓ Wheels built in: $WHEELS_DIR"
echo ""
echo "Next steps:"
echo "1. Copy the wheels/ directory to your Raspberry Pi"
echo "2. On the Pi, run: docker compose up -d"
echo "   (The Dockerfile will use local wheels if available)"
