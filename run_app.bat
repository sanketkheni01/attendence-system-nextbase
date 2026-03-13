@echo off
echo Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not added to PATH. 
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Installing dependencies...
py -m pip install -r requirements.txt

echo Starting Attendance Management System...
py -m streamlit run app.py

pause
