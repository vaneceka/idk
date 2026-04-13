#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/main.py" ]]; then
  CHECKER_DIR="${ROOT_DIR}"
elif [[ -f "${ROOT_DIR}/checker/main.py" ]]; then
  CHECKER_DIR="${ROOT_DIR}/checker"
else
  echo "[ERR] main.py nebyl nalezen ani v: ${ROOT_DIR}/main.py ani ${ROOT_DIR}/checker/main.py" >&2
  exit 1
fi

MAIN_PY="${CHECKER_DIR}/main.py"

is_python_310_plus() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

pick_python() {
  local candidates=(
    "${CHECKER_DIR}/.venv/bin/python3"
    "${CHECKER_DIR}/.venv/bin/python"
  )

  local cmd
  for cmd in "${candidates[@]}"; do
    if [[ -x "$cmd" ]] && is_python_310_plus "$cmd"; then
      echo "$cmd"
      return 0
    fi
  done

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

PYTHON_BIN="$(pick_python)" || {
  echo "[ERR] Nebyl nalezen použitelný Python 3.10 nebo novější." >&2
  echo "      Nejprve spusť instalaci nebo doinstaluj novější Python." >&2
  exit 1
}

cd "$CHECKER_DIR"
"$PYTHON_BIN" "$MAIN_PY" "$@"