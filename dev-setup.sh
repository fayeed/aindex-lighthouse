#!/usr/bin/env bash
set -euo pipefail

echo "Installing ai_lighthouse_core and ai_lighthouse in editable mode into the active Python environment..."

python -m pip install -e ./core
python -m pip install -e ./cli  

echo "Done. You can now import ai_lighthouse_core and ai_lighthouse in this environment."
