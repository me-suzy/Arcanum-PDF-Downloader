@echo off
echo ========================================
echo ARCANUM AUTOMATION - START
echo ========================================
echo.
echo This will start the automation setup.
echo The window will stay open.
echo.
echo Press any key to continue...
pause >nul

echo.
echo Starting automation setup...
echo.

REM Change to the correct directory first
cd /d "%~dp0"
echo Current directory: %cd%

REM Ruleaza scriptul PowerShell pentru crearea task-ului
echo Running PowerShell script to create scheduled task...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0Create_Arcanum_Scheduled_Task.ps1"

echo.
echo ========================================
echo AUTOMATION SETUP COMPLETED
echo ========================================
echo.
echo The scheduled task has been created.
echo It will run daily at 9:00 AM.
echo.
echo To check status, run: check_task_status.bat
echo.
echo Press any key to exit...
pause >nul
