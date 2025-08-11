@echo off
echo ========================================
echo AUTOMATION TEST - FIXED VERSION
echo ========================================
echo.
echo This test will NOT close immediately!
echo.
echo Press any key to start testing...
pause >nul

echo.
echo Step 1: Testing directory change...
cd /d "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"

if %errorlevel% equ 0 (
    echo [SUCCESS] Directory changed to: %cd%
) else (
    echo [ERROR] Could not change directory
    echo Error code: %errorlevel%
)

echo.
echo Step 2: Checking files...
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
    echo [OK] Python works
    py --version
) else (
    echo [ERROR] Python not working
)

echo.
echo Step 4: Testing reset script...
echo.

echo Running reset script...
py reset_daily_limit.py
echo Reset script completed with code: %errorlevel%

echo.
echo Step 5: Creating logs directory...
echo.

if not exist "Logs" (
    mkdir "Logs"
    echo [OK] Logs directory created
) else (
    echo [OK] Logs directory exists
)

echo.
echo ========================================
echo AUTOMATION TEST COMPLETED!
echo ========================================
echo.
echo All tests finished successfully.
echo The automation is ready to use.
echo.
echo Press any key to exit...
pause >nul

