@echo off
REM ============================================================================
REM Script CMD simplu pentru crearea task-ului planificat
REM ALTERNATIVĂ la scriptul PowerShell
REM MODIFICAT: Calea corectă și verificări pentru reset_daily_limit.py
REM ============================================================================

echo ============================================================================
echo CREARE AUTOMATĂ WINDOWS SCHEDULED TASK PENTRU ARCANUM PDF DOWNLOADER
echo ============================================================================
echo.

REM Verifică dacă rulează ca Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo EROARE: Acest script trebuie rulat ca Administrator!
    echo Click dreapta pe Command Prompt ^> Run as administrator
    echo.
    pause
    exit /b 1
)

echo ✅ Rulează ca Administrator - OK
echo.

REM Configurări (CALEA TA REALĂ!)
set TASK_NAME=Arcanum_PDF_Downloader_Daily
set SCRIPT_PATH="E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"
set BATCH_FILE=%SCRIPT_PATH%\run_arcanum_daily.bat
set PYTHON_SCRIPT=%SCRIPT_PATH%\Claude-FINAL 2 - BUN Sterge pdf pe D.py
set RESET_SCRIPT=%SCRIPT_PATH%\reset_daily_limit.py

echo Configurații curente:
echo   Nume task: %TASK_NAME%
echo   Cale script: %SCRIPT_PATH%
echo   Batch file: %BATCH_FILE%
echo   Python script: %PYTHON_SCRIPT%
echo   Reset script: %RESET_SCRIPT%
echo.

REM Verifică dacă fișierele există
if not exist %SCRIPT_PATH% (
    echo ❌ EROARE: Directorul %SCRIPT_PATH% nu există!
    echo Creează directorul și copiază fișierele acolo.
    pause
    exit /b 1
)

if not exist %BATCH_FILE% (
    echo ❌ EROARE: Fișierul %BATCH_FILE% nu există!
    echo Asigură-te că ai copiat run_arcanum_daily.bat în director.
    pause
    exit /b 1
)

if not exist %PYTHON_SCRIPT% (
    echo ❌ EROARE: Scriptul Python nu există: %PYTHON_SCRIPT%
    echo Asigură-te că ai copiat scriptul Python în director.
    pause
    exit /b 1
)

if not exist %RESET_SCRIPT% (
    echo ❌ EROARE: Scriptul de resetare nu există: %RESET_SCRIPT%
    echo Asigură-te că ai copiat reset_daily_limit.py în director.
    pause
    exit /b 1
)

echo ✅ Toate fișierele există - OK
echo.

REM Șterge task-ul existent dacă există
echo Verific dacă task-ul există deja...
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠ Task-ul %TASK_NAME% există deja!
    set /p choice="Dorești să-l ștergi și să creezi unul nou? (Y/N): "
    if /i "!choice!"=="Y" (
        echo Șterg task-ul vechi...
        schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
        echo ✅ Task-ul vechi a fost șters
    ) else (
        echo Operațiune anulată.
        pause
        exit /b 0
    )
)

echo.
echo 🔧 Creez noul task planificat...
echo.

REM Creează task-ul nou cu schtasks - SETĂRI ÎMBUNĂTĂȚITE pentru continuitate
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "cmd.exe /c \"%BATCH_FILE%\"" ^
    /sc daily ^
    /st 09:00 ^
    /ru "%USERNAME%" ^
    /rl highest ^
    /it ^
    /f

REM Adaugă setări suplimentare pentru continuitate
echo 🔧 Configurez setări avansate pentru continuitate...
schtasks /change /tn "%TASK_NAME%" /enable
schtasks /change /tn "%TASK_NAME%" /ri 1440
schtasks /change /tn "%TASK_NAME%" /du 23:59

echo ✅ Task configurat cu setări de continuitate

REM Verifică dacă task-ul a fost creat cu succes
if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCES! Task-ul a fost creat cu succes!
    echo.
    echo ============================================================================
    echo INFORMAȚII TASK CREAT:
    echo ============================================================================
    echo Nume task: %TASK_NAME%
    echo Frecvență: Zilnic la 9:00 AM
    echo Rulează ca: %USERNAME%
    echo Comandă: cmd.exe /c "%BATCH_FILE%"
    echo.
    echo 📋 URMĂTORII PAȘI:
    echo 1. Testează batch file-ul manual: %BATCH_FILE%
    echo 2. Task-ul va rula automat mâine la 9:00 AM
    echo 3. Pentru a opri: deschide Task Scheduler și dezactivează '%TASK_NAME%'
    echo 4. Verifică progresul în fișierul state.json din %SCRIPT_PATH%
    echo.
    echo 🎯 IMPORTANT: Task-ul va continua ZILNIC chiar dacă atinge limita!
    echo Va reseta automat limita în fiecare zi și va continua de unde a rămas.
    echo.
    
    REM Oferă opțiunea de testare
    set /p test_choice="🔧 Dorești să testezi task-ul acum? (Y/N): "
    if /i "!test_choice!"=="Y" (
        echo.
        echo 🚀 Pornesc task-ul pentru test...
        schtasks /run /tn "%TASK_NAME%"
        echo ✅ Task-ul a fost pornit pentru test
        echo Verifică dacă se deschide o fereastră cu scriptul
    )
    
) else (
    echo.
    echo ❌ EROARE la crearea task-ului!
    echo Încearcă să creezi task-ul manual prin Task Scheduler:
    echo 1. Apasă Win+R, scrie 'taskschd.msc', Enter
    echo 2. Create Basic Task...
    echo 3. Nume: %TASK_NAME%
    echo 4. Trigger: Daily, 9:00 AM
    echo 5. Action: Start program - cmd.exe
    echo 6. Arguments: /c "%BATCH_FILE%"
)

echo.
echo ============================================================================
echo CONFIGURARE FINALIZATĂ
echo ============================================================================
echo.
pause