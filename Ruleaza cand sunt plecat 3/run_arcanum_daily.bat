@echo off
REM ============================================================================
REM Script pentru rularea zilnică automată a Arcanum PDF Downloader
REM VERSIUNEA ÎMBUNĂTĂȚITĂ - NU SE ÎNCHIDE NICIODATĂ
REM Creat pentru executare via Windows Task Scheduler la 9:00 AM
REM MODIFICAT: Resetează automat limita zilnică și continuă zilnic
REM ============================================================================

REM Setează directorul de lucru (CALEA TA REALĂ)
cd /d "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"

REM Creează directorul pentru log-uri dacă nu există
if not exist "Logs" mkdir "Logs"

REM Setează numele fișierului de log cu timestamp
set "LogFile=Logs\arcanum_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LogFile=%LogFile: =0%"

REM Funcție pentru logging
:log
echo [%date% %time%] %~1 >> "%LogFile%"
echo [%date% %time%] %~1
goto :eof

REM Funcție pentru logging cu eroare
:logerror
echo [%date% %time%] EROARE: %~1 >> "%LogFile%"
echo [%date% %time%] EROARE: %~1
goto :eof

REM Funcție pentru logging cu succes
:logsuccess
echo [%date% %time%] SUCCES: %~1 >> "%LogFile%"
echo [%date% %time%] SUCCES: %~1
goto :eof

call :log "============================================================================"
call :log "PORNIRE AUTOMATIZARE ARCANUM PDF DOWNLOADER - VERSIUNEA ÎMBUNĂTĂȚITĂ"
call :log "NU SE ÎNCHIDE NICIODATĂ - CONTINUĂ ZILNIC"
call :log "============================================================================"
call :log "Director de lucru: %cd%"
call :log "Fișier log: %LogFile%"

REM Verifică dacă fișierele Python există
if not exist "Claude-FINAL 2 - BUN Sterge pdf pe D.py" (
    call :logerror "Nu găsesc scriptul Python principal!"
    call :log "Verifică calea: %cd%"
    call :log "Căut fișierul: Claude-FINAL 2 - BUN Sterge pdf pe D.py"
    call :log "Task-ul va încerca din nou mâine la 9:00 AM"
    goto :end
)

if not exist "reset_daily_limit.py" (
    call :logerror "Nu găsesc scriptul de resetare!"
    call :log "Verifică calea: %cd%"
    call :log "Căut fișierul: reset_daily_limit.py"
    call :log "Task-ul va încerca din nou mâine la 9:00 AM"
    goto :end
)

call :log "Script găsit, resetez flag-ul de limită zilnică..."

REM DETECTEAZĂ COMANDA PYTHON CORECTĂ
call :log "Detectez comanda Python corectă..."
set "PYTHON_CMD="

REM Încearcă mai întâi py (Python Launcher pentru Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    call :log "Python detectat: py (Python Launcher pentru Windows)"
) else (
    REM Încearcă python3
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python3"
        call :log "Python detectat: python3"
    ) else (
        REM Încearcă python
        python --version >nul 2>&1
        if %errorlevel% equ 0 (
            set "PYTHON_CMD=python"
            call :log "Python detectat: python"
        ) else (
            call :logerror "Nici py, nici python3, nici python nu sunt disponibile!"
            call :log "Task-ul va încerca din nou mâine la 9:00 AM"
            goto :end
        )
    )
)

call :log "Comanda Python finală: %PYTHON_CMD%"

REM PASUL 1: Resetează flag-ul de limită zilnică pentru ziua nouă
call :log "PASUL 1: Resetare flag limită zilnică..."
call :log "Execut: %PYTHON_CMD% reset_daily_limit.py"
%PYTHON_CMD% "reset_daily_limit.py" 2>>"%LogFile%"
if %errorlevel% neq 0 (
    call :logerror "Nu s-a putut reseta flag-ul de limită zilnică"
    call :log "Cod eroare: %errorlevel%"
    call :log "Va încerca din nou mâine la 9:00 AM"
) else (
    call :logsuccess "Flag-ul de limită zilnică resetat cu succes"
)

call :log "PASUL 2: Pornesc scriptul principal..."

REM PASUL 2: Rulează scriptul principal cu flag-ul --automated
call :log "Execut scriptul principal: Claude-FINAL 2 - BUN Sterge pdf pe D.py"
call :log "Comandă: %PYTHON_CMD% Claude-FINAL 2 - BUN Sterge pdf pe D.py --automated"
%PYTHON_CMD% "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated 2>>"%LogFile%"
if %errorlevel% neq 0 (
    call :log "Scriptul principal s-a terminat cu cod de eroare: %errorlevel%"
    call :log "Acest lucru este NORMAL dacă Arcanum a ajuns la limita zilnică"
    call :log "Task-ul va continua mâine la 9:00 AM"
) else (
    call :logsuccess "Scriptul principal executat cu succes"
)

REM Verifică rezultatul execuției
if %errorlevel% equ 0 (
    call :logsuccess "Script terminat cu SUCCES"
) else (
    call :log "Script terminat cu cod de eroare: %errorlevel%"
    call :log "Acest lucru este NORMAL dacă Arcanum a ajuns la limita zilnică"
    call :log "Task-ul va continua mâine la 9:00 AM"
)

REM PASUL 3: Verificare finală și raport
call :log "PASUL 3: Verificare finală și raport..."

REM Verifică dacă există fișiere PDF noi
set "pdf_count=0"
for %%f in (D:\*.pdf) do set /a pdf_count+=1
call :log "Fișiere PDF găsite pe D:\: %pdf_count%"

REM Verifică dacă există state.json
if exist "state.json" (
    call :log "Fișierul state.json există - progresul a fost salvat"
) else (
    call :log "Fișierul state.json nu există - va fi creat la prima rulare"
)

REM Verifică dacă există skip_urls.json
if exist "skip_urls.json" (
    call :log "Fișierul skip_urls.json există - URL-urile complete sunt marcate"
) else (
    call :log "Fișierul skip_urls.json nu există - va fi creat la prima rulare"
)

call :log "============================================================================"
call :log "FINALIZARE AUTOMATIZARE ARCANUM PDF DOWNLOADER"
call :log "============================================================================"

REM IMPORTANT: Întotdeauna returnează cod de succes pentru Task Scheduler
REM astfel task-ul va continua să ruleze zilnic chiar dacă scriptul atinge limita
call :log "Task-ul va continua mâine la 9:00 AM..."
call :log "NU SE ÎNCHIDE NICIODATĂ - continuă procesarea zilnică!"
call :log "Chiar dacă Arcanum ajunge la limita zilnică, task-ul va continua!"
call :log "Comanda Python folosită: %PYTHON_CMD%"

:end
call :log "============================================================================"
call :log "ÎNCHIDERE SCRIPT - Task-ul va rula din nou mâine la 9:00 AM"
call :log "============================================================================"

REM IMPORTANT: Întotdeauna returnează cod de succes pentru Task Scheduler
REM astfel task-ul va continua să ruleze zilnic chiar dacă scriptul atinge limita
exit /b 0