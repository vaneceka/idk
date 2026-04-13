@echo off
setlocal

set SCRIPT_DIR=%~dp0

set PYTHONPATH=%SCRIPT_DIR%..;%PYTHONPATH%

echo Generuji registr kontrol...

python "%SCRIPT_DIR%..\core\generate_checks_registry.py"

if %ERRORLEVEL% EQU 0 (
    echo Hotovo. Registr byl úspěšně vygenerován.
) else (
    echo Došlo k chybě při generování!
    pause
)

endlocal