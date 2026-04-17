@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%LocalAppData%\Python\pythoncore-3.14-64\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python not found at:
    echo %PYTHON_EXE%
    exit /b 1
)

cd /d "%PROJECT_DIR%"
"%PYTHON_EXE%" app.py

