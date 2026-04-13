#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}/.."

echo "Generuji registr kontrol..."

"${SCRIPT_DIR}/../.venv/bin/python" "${SCRIPT_DIR}/../core/generate_checks_registry.py"

if [ $? -eq 0 ]; then
    echo "Hotovo."
else
    echo "Chyba při generování registru!"
    exit 1
fi