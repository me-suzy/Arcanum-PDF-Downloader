@echo off
echo Configurez Task Scheduler pentru ArcanumDownloader...

REM Verifică dacă rulezi ca Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo EROARE: Trebuie sa rulezi ca Administrator!
    echo Click dreapta pe acest script si alege "Run as administrator"
    pause
    exit /b 1
)

REM Creează task-ul
schtasks /create /tn "ArcanumDownloader" /tr "\"e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat in concediu\daily_arcanum_start.bat\"" /sc daily /st 09:00 /ru "%username%" /rl highest /f

if %errorlevel% == 0 (
    echo ✅ Task-ul a fost creat cu succes!
    echo Va rula zilnic la 09:00
) else (
    echo ❌ Eroare la crearea task-ului!
)

pause