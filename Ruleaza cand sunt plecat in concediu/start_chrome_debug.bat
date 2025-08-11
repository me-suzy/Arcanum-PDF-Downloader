@echo off
echo [%date% %time%] Pornesc Chrome cu remote debugging...

REM Oprește Chrome existent
tasklist /fi "imagename eq chrome.exe" 2>NUL | find /i "chrome.exe" >NUL
if not errorlevel 1 (
    echo Opresc Chrome-ul existent...
    taskkill /f /im chrome.exe >nul 2>&1
    timeout /t 3 /nobreak >nul
)

REM Setează căile
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
set PROFILE_DIR="C:/Users/necul/AppData/Local/Google/Chrome/User Data/Default"

REM Pornește Chrome cu debugging
start /min "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir=%PROFILE_DIR% --disable-extensions

echo ✅ Chrome pornit cu remote debugging pe portul 9222
timeout /t 3 /nobreak >nul