@echo off
setlocal

set "PYTHON_EXE=%LocalAppData%\Python\pythoncore-3.14-64\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python not found at:
    echo %PYTHON_EXE%
    exit /b 1
)

"%PYTHON_EXE%" -m pip install --upgrade pip

