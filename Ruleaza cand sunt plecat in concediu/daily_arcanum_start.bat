@echo off
REM ========================================================
REM daily_arcanum_start.bat - Script pentru pornirea zilnică automată
REM ========================================================

echo [%date% %time%] === PORNIRE AUTOMATA ARCANUM DOWNLOADER ===
echo.

REM Navighează la folderul cu script-ul Python
cd /d "e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome"

REM Verifică dacă fișierul Python există
if not exist "FINAL_AUTO_with_disk_monitoring.py" (
    echo EROARE: Nu găsesc fișierul Python principal!
    echo Caut in folderul: %cd%
    dir *.py
    echo [%date% %time%] EROARE: Fisier Python lipsa >> "D:\daily_run_log.txt"
    pause
    exit /b 1
)

REM 1. Pornește Chrome cu remote debugging (în background)
echo [%date% %time%] Pornesc Chrome cu remote debugging...
start /min "Chrome Debug" start_chrome_debug.bat

REM Aștept 10 secunde pentru Chrome să pornească complet
echo [%date% %time%] Astept 10 secunde pentru Chrome sa porneasca...
timeout /t 10 /nobreak >nul

REM 2. Verifică spațiul pe disk înainte de start
echo [%date% %time%] Verific spatiul pe disk...
for /f "tokens=3" %%a in ('dir D:\ ^| findstr "bytes free"') do set FREE_SPACE=%%a
echo Spatiu liber pe D: %FREE_SPACE% bytes

REM 3. Rulează script-ul Python de download
echo [%date% %time%] Pornesc procesul principal de download...
echo --------------------------------------------------------
python "FINAL_AUTO_with_disk_monitoring.py"
set PYTHON_EXIT_CODE=%errorlevel%
echo --------------------------------------------------------
echo [%date% %time%] Procesul Python s-a terminat cu codul: %PYTHON_EXIT_CODE%

REM 4. Raportează rezultatul
if %PYTHON_EXIT_CODE% == 0 (
    echo [%date% %time%] ✅ SUCCESS: Procesul de download s-a incheiat cu succes!
    echo [%date% %time%] SUCCESS: Download complet >> "D:\daily_run_log.txt"
) else (
    echo [%date% %time%] ⚠️ WARNING: Procesul de download a intampinat probleme! Exit code: %PYTHON_EXIT_CODE%
    echo [%date% %time%] WARNING: Exit code %PYTHON_EXIT_CODE% >> "D:\daily_run_log.txt"
)

REM 5. Verifică din nou spațiul pe disk după procesare
echo [%date% %time%] Verific spatiul final pe disk...
for /f "tokens=3" %%a in ('dir D:\ ^| findstr "bytes free"') do set FINAL_FREE_SPACE=%%a
echo Spatiu liber final pe D: %FINAL_FREE_SPACE% bytes

REM 6. Salvează log-ul de finalizare
echo [%date% %time%] Procesul zilnic finalizat - Exit: %PYTHON_EXIT_CODE% >> "D:\daily_run_log.txt"

REM 7. Generează raport rapid de progres (dacă monitor_progress.py există)
if exist "monitor_progress.py" (
    echo [%date% %time%] Generez raport de progres...
    python monitor_progress.py >> "D:\daily_run_log.txt" 2>&1
)

REM 8. Cleanup opțional - nu opresc Chrome în caz că mai urmează procesări
REM taskkill /f /im chrome.exe >nul 2>&1

echo.
echo [%date% %time%] === PROCESUL ZILNIC FINALIZAT ===
echo Verifica log-urile in D:\ pentru detalii complete
echo.

REM Pentru debugging - șterge următoarea linie în producție
REM pause

exit /b %PYTHON_EXIT_CODE%


REM ========================================================
REM start_chrome_debug.bat - ACTUALIZAT
REM ========================================================
REM
REM Salvează următorul conținut în start_chrome_debug.bat:
REM
REM @echo off
REM echo [%date% %time%] Pornesc Chrome cu remote debugging...
REM
REM REM Oprește orice instanță Chrome existentă (cu verificare)
REM tasklist /fi "imagename eq chrome.exe" 2>NUL | find /i "chrome.exe" >NUL
REM if not errorlevel 1 (
REM     echo Opresc Chrome-ul existent...
REM     taskkill /f /im chrome.exe >nul 2>&1
REM     timeout /t 3 /nobreak >nul
REM ) else (
REM     echo Chrome nu ruleaza deja.
REM )
REM
REM REM Pornește Chrome pe profilul Default cu remote debugging activat
REM set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
REM set PROFILE_DIR="C:/Users/necul/AppData/Local/Google/Chrome/User Data/Default"
REM
REM REM Verifică dacă Chrome există
REM if not exist %CHROME_PATH% (
REM     echo EROARE: Chrome nu a fost gasit la calea: %CHROME_PATH%
REM     pause
REM     exit /b 1
REM )
REM
REM REM Pornește Chrome minimizat în background cu debugging
REM echo Pornesc Chrome cu debugging pe portul 9222...
REM start /min "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir=%PROFILE_DIR% --disable-extensions --disable-plugins --disable-images
REM
REM REM Așteptă și verifică că s-a pornit
REM timeout /t 5 /nobreak >nul
REM tasklist /fi "imagename eq chrome.exe" 2>NUL | find /i "chrome.exe" >NUL
REM if not errorlevel 1 (
REM     echo ✅ Chrome pornit cu succes cu remote debugging pe portul 9222
REM ) else (
REM     echo ❌ EROARE: Chrome nu a pornit corect!
REM     pause
REM     exit /b 1
REM )
REM
REM timeout /t 2 /nobreak >nul


REM ========================================================
REM setup_task_scheduler.bat - Pentru configurare automată
REM (RULEAZĂ CA ADMINISTRATOR)
REM ========================================================
REM
REM Salvează următorul conținut în setup_task_scheduler.bat:
REM
REM @echo off
REM echo ========================================================
REM echo    CONFIGURARE TASK SCHEDULER PENTRU ARCANUM DOWNLOADER
REM echo ========================================================
REM echo.
REM
REM REM Verifică privilegiile de Administrator
REM net session >nul 2>&1
REM if %errorLevel% neq 0 (
REM     echo ❌ EROARE: Trebuie sa rulezi ca Administrator!
REM     echo Click dreapta pe acest script si alege "Run as administrator"
REM     pause
REM     exit /b 1
REM )
REM
REM echo ✅ Privilegii Administrator detectate
REM echo.
REM
REM REM Șterge task-ul existent (dacă există)
REM echo Sterg task-ul existent (daca exista)...
REM schtasks /delete /tn "ArcanumDownloader" /f >nul 2>&1
REM
REM REM Creează task-ul nou
REM echo Creez task-ul nou pentru rulare zilnica la 09:00...
REM schtasks /create /tn "ArcanumDownloader" /tr "\"e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\daily_arcanum_start.bat\"" /sc daily /st 09:00 /ru "%username%" /rl highest /f
REM
REM if %errorlevel% == 0 (
REM     echo ✅ Task-ul "ArcanumDownloader" a fost creat cu succes!
REM     echo    📅 Program: Zilnic la 09:00
REM     echo    👤 User: %username%
REM     echo    🔧 Privilegii: Highest
REM ) else (
REM     echo ❌ EROARE la crearea task-ului! Cod eroare: %errorlevel%
REM     pause
REM     exit /b 1
REM )
REM
REM REM Creează și task-ul pentru monitorizare (opțional)
REM echo.
REM echo Creez task-ul pentru monitorizare zilnica la 20:00...
REM schtasks /delete /tn "ArcanumMonitor" /f >nul 2>&1
REM schtasks /create /tn "ArcanumMonitor" /tr "\"python e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\monitor_progress.py\"" /sc daily /st 20:00 /ru "%username%" /f
REM
REM if %errorlevel% == 0 (
REM     echo ✅ Task-ul "ArcanumMonitor" a fost creat cu succes!
REM ) else (
REM     echo ⚠️ Task-ul pentru monitorizare nu a putut fi creat (nu e critic)
REM )
REM
REM echo.
REM echo ========================================================
REM echo                    ✅ CONFIGURARE COMPLETA!
REM echo ========================================================
REM echo.
REM echo TASK-uri create:
REM echo   📥 ArcanumDownloader - Zilnic la 09:00
REM echo   📊 ArcanumMonitor    - Zilnic la 20:00 (opțional)
REM echo.
REM echo COMENZI UTILE:
REM echo   Verifica status: schtasks /query /tn "ArcanumDownloader"
REM echo   Ruleaza manual:  schtasks /run /tn "ArcanumDownloader"
REM echo   Opreste:         schtasks /end /tn "ArcanumDownloader"
REM echo   Sterge:          schtasks /delete /tn "ArcanumDownloader" /f
REM echo.
REM echo 🎯 Sistemul va rula automat zilnic de acum!
REM echo 📁 Log-uri: D:\daily_run_log.txt si D:\arcanum_daily_log.txt
REM echo 🗂️ Progres: D:\state.json
REM echo.
REM pause