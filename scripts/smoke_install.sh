#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

python3 -m pip install --upgrade pip build
rm -rf dist build
python3 -m build

VENV="$(mktemp -d)/forgebench-smoke-venv"
python3 -m venv "${VENV}"
"${VENV}/bin/pip" install --upgrade pip
"${VENV}/bin/pip" install dist/forgebench-*.whl

"${VENV}/bin/forgebench" --version
"${VENV}/bin/forgebench" --help
"${VENV}/bin/forgebench" doctor
"${VENV}/bin/python" -c "import forgebench; assert forgebench.__version__ == '0.9.0'"

echo "smoke_install: ok"