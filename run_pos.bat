@echo off
setlocal

cd /d "%~dp0"
set "HOST=127.0.0.1"
set "PORT=8000"
set "LOGIN_URL=http://%HOST%:%PORT%/login/"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
        set "PYTHON=py -3"
    ) else (
        set "PYTHON=python"
    )
)

echo Starting POS Enghing on http://%HOST%:%PORT% ...
echo Opening login page: %LOGIN_URL%

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process '%LOGIN_URL%'"

%PYTHON% manage.py runserver %HOST%:%PORT%

endlocal
