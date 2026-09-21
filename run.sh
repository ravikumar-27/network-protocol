#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=== Dual-Panel Activity & Protocol Visualizer ==="
echo "Python Version: $(python3 --version)"

if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

PORT="${PORT:-5005}"
echo "[*] Launching server on http://localhost:$PORT"
./venv/bin/python app.py
