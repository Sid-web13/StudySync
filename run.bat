@echo off
setlocal
echo ========================================================
echo [StudySync] Smart Personalized Academic Mentorship Platform
echo [StudySync] SIH Problem Statement 26207: Smart Education
echo ========================================================

REM Resolve Python executable
set "PYTHON_EXE=python"
where %PYTHON_EXE% >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "%LOCALAPPDATA%\Python\pythoncore-3.15-64\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Python\pythoncore-3.15-64\python.exe"
    ) else (
        set "PYTHON_EXE=py"
    )
)

echo [StudySync] Running idempotent database seeder...
"%PYTHON_EXE%" backend\seed.py
if %ERRORLEVEL% neq 0 (
    echo [StudySync] Warning: Seeder reported an error or is already populated.
)

echo [StudySync] Launching FastAPI backend server on http://localhost:8000 ...
start "StudySync Server (Port 8000)" "%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo [StudySync] Waiting 3 seconds for server startup...
timeout /t 3 /nobreak >nul

echo [StudySync] Launching web browser at http://localhost:8000 ...
start http://localhost:8000

echo.
echo ========================================================
echo StudySync is running at: http://localhost:8000
echo Evaluator Demo Credentials:
echo   Email:    siddharth@studysync.edu
echo   Password: Password@123
echo To stop the server at any time, run: stop.bat
echo ========================================================
endlocal
