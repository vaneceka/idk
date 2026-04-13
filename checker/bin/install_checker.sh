#!/usr/bin/env bash
set -euo pipefail

err() { echo "[ERR] $*" >&2; exit 1; }
info() { echo "[OK] $*"; }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -f "$ROOT_DIR/requirements.txt" ] && [ -f "$ROOT_DIR/main.py" ]; then
  CHECKER_DIR="$ROOT_DIR"
elif [ -f "$ROOT_DIR/checker/requirements.txt" ] && [ -f "$ROOT_DIR/checker/main.py" ]; then
  CHECKER_DIR="$ROOT_DIR/checker"
else
  err "Nelze najít checker (requirements.txt + main.py) ani v $ROOT_DIR ani v $ROOT_DIR/checker"
fi

REQ_FILE="$CHECKER_DIR/requirements.txt"
VENV_DIR="$CHECKER_DIR/.venv"

is_python_310_plus() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

find_python_310_plus() {
  if command -v python3 >/dev/null 2>&1 && is_python_310_plus python3; then
    echo "python3"
    return 0
  fi

  if command -v python >/dev/null 2>&1 && is_python_310_plus python; then
    echo "python"
    return 0
  fi

  return 1
}

PYTHON_CMD="$(find_python_310_plus)" || err "Nebyl nalezen Python 3.10 nebo novější."

[ -f "$REQ_FILE" ] || err "Chybí $REQ_FILE"

info "Používám checker dir: $CHECKER_DIR"
info "Používám interpreter: $PYTHON_CMD"
info "Vytvářím venv: $VENV_DIR"

rm -rf "$VENV_DIR"
"$PYTHON_CMD" -m venv "$VENV_DIR"

if [ -x "$VENV_DIR/bin/python3" ]; then
  VENV_PY="$VENV_DIR/bin/python3"
elif [ -x "$VENV_DIR/bin/python" ]; then
  VENV_PY="$VENV_DIR/bin/python"
else
  err "Ve virtuálním prostředí nebyl nalezen python ani python3."
fi

is_python_310_plus "$VENV_PY" || err "Vytvořené virtuální prostředí nepoužívá Python 3.10+."

info "Instaluji requirements..."
"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install -r "$REQ_FILE"

info "Hotovo."
echo Spusteni napovedy:       ./bin/run_checker.sh --help