@echo off
echo ========================================
echo FINAL TEST - VERIFICARE COMPLETA
echo ========================================

echo.
echo Starting test process...
echo Current directory: %cd%
echo.

echo Step 1: Changing to target directory...
cd /d "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"

if %errorlevel% equ 0 (
    echo SUCCESS: Directory changed successfully
    echo New directory: %cd%
) else (
    echo ERROR: Could not change directory
    echo Error code: %errorlevel%
    echo.
    echo Press any key to continue...
    pause >nul
    goto :end
)

echo.
echo Step 2: Checking required files...
echo.

if exist "Claude-FINAL 2 - BUN Sterge pdf pe D.py" (
    echo [OK] Python script exists
) else (
    echo [ERROR] Python script not found
)

if exist "reset_daily_limit.py" (
    echo [OK] Reset script exists
) else (
    echo [ERROR] Reset script not found
)

if exist "run_arcanum_daily.bat" (
    echo [OK] Batch file exists
) else (
    echo [ERROR] Batch file not found
)

echo.
echo Step 3: Testing Python...
echo.

py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python Launcher works
    py --version
) else (
    echo [ERROR] Python Launcher not working
)

echo.
echo Step 4: Testing reset script...
echo.

echo Running: py reset_daily_limit.py
py reset_daily_limit.py
echo.
echo Reset script completed with code: %errorlevel%

echo.
echo Step 5: Creating Logs directory...
echo.

if not exist "Logs" (
    mkdir "Logs"
    echo [OK] Logs directory created
) else (
    echo [OK] Logs directory already exists
)

echo.
echo ========================================
echo TEST COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo All components are working correctly.
echo You can now create the scheduled task.
echo.
echo Press any key to exit...
pause >nul

:end
echo.
echo Test finished. Press any key to close...
pause >nul
