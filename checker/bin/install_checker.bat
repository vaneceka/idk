@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"

if exist "%ROOT_DIR%\main.py" if exist "%ROOT_DIR%\requirements.txt" (
  set "CHECKER_DIR=%ROOT_DIR%"
) else if exist "%ROOT_DIR%\checker\main.py" if exist "%ROOT_DIR%\checker\requirements.txt" (
  set "CHECKER_DIR=%ROOT_DIR%\checker"
) else (
  echo [ERR] Nelze najit checker ^(main.py + requirements.txt^) ani v "%ROOT_DIR%" ani v "%ROOT_DIR%\checker"
  exit /b 1
)

set "REQ_FILE=%CHECKER_DIR%\requirements.txt"
set "VENV_DIR=%CHECKER_DIR%\.venv"
set "PYTHON_CMD="

py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3.12"

if not defined PYTHON_CMD (
  py -3.11 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=py -3.11"
)

if not defined PYTHON_CMD (
  py -3.10 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=py -3.10"
)

if not defined PYTHON_CMD (
  echo [ERR] Nebyl nalezen Python 3.10 nebo novejsi.
  echo       Nainstaluj Python 3.10+ a zkus to znovu.
  exit /b 1
)

if not exist "%REQ_FILE%" (
  echo [ERR] Chybi requirements.txt: "%REQ_FILE%"
  exit /b 1
)

echo [OK] Pouzivam checker dir: "%CHECKER_DIR%"
echo [OK] Pouzivam interpreter: %PYTHON_CMD%
echo [OK] Vytvarim venv: "%VENV_DIR%"

if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"

%PYTHON_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 exit /b 1

if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo [ERR] Ve virtualnim prostredi nebyl nalezen python.exe
  exit /b 1
)

"%VENV_DIR%\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo [ERR] Virtualni prostredi nepouziva Python 3.10+
  exit /b 1
)

echo [OK] Instaluji requirements...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REQ_FILE%"
if errorlevel 1 exit /b 1

echo.
echo [OK] Hotovo.
echo Aktivace ^(volitelne^):  cd "%CHECKER_DIR%" ^&^& .venv\Scripts\activate
echo Spusteni napovedy:       .\bin\run_checker.bat --help