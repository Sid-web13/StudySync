@echo off
setlocal
echo ========================================================
echo [StudySync] Terminating StudySync Server on Port 8000...
echo ========================================================

set FOUND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [StudySync] Killing process PID: %%a listening on port 8000...
    taskkill /F /PID %%a >nul 2>&1
    set FOUND=1
)

if %FOUND% equ 1 (
    echo [StudySync] Server process terminated. Port 8000 is now free.
) else (
    echo [StudySync] No processes found actively listening on port 8000.
)

echo ========================================================
endlocal
