@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"

if exist "%ROOT_DIR%\main.py" (
  set "CHECKER_DIR=%ROOT_DIR%"
) else if exist "%ROOT_DIR%\checker\main.py" (
  set "CHECKER_DIR=%ROOT_DIR%\checker"
) else (
  echo [ERR] main.py nebyl nalezen ani v: "%ROOT_DIR%\main.py" ani "%ROOT_DIR%\checker\main.py"
  exit /b 1
)

set "MAIN_PY=%CHECKER_DIR%\main.py"
set "VENV_PY=%CHECKER_DIR%\.venv\Scripts\python.exe"
set "PYTHON_BIN="

if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_BIN=%VENV_PY%"
  )
)

if not defined PYTHON_BIN (
  py -3.12 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PYTHON_BIN=py -3.12"
)

if not defined PYTHON_BIN (
  py -3.11 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PYTHON_BIN=py -3.11"
)

if not defined PYTHON_BIN (
  py -3.10 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PYTHON_BIN=py -3.10"
)

if not defined PYTHON_BIN (
  echo [ERR] Nebyl nalezen Python 3.10 nebo novejsi.
  echo       Nejprve spust instalaci nebo doinstaluj novy Python.
  exit /b 1
)

pushd "%CHECKER_DIR%"
%PYTHON_BIN% "%MAIN_PY%" %*
set "RC=%ERRORLEVEL%"
popd

exit /b %RC%