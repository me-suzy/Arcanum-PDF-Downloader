@echo off
REM ============================================================================
REM Script de verificare rapidă pentru statusul task-ului Arcanum
REM Verifică dacă task-ul este activ și când va rula următoarea dată
REM ============================================================================

echo [%date% %time%] VERIFICARE STATUS TASK ARCANUM
echo ============================================================================

REM Verifică dacă task-ul există
echo [%date% %time%] Verificare existență task...
schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Task-ul "Arcanum_PDF_Downloader_Daily_Enhanced" există
    echo.
    
    echo [%date% %time%] Informații detaliate task:
    echo ----------------------------------------------------------------------------
    schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /fo list | findstr /i "Task\|Next\|Status\|Last\|State"
    echo ----------------------------------------------------------------------------
    
    echo.
    echo [%date% %time%] Verificare status Task Scheduler...
    echo ----------------------------------------------------------------------------
    schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /fo table
    echo ----------------------------------------------------------------------------
    
) else (
    echo ❌ Task-ul "Arcanum_PDF_Downloader_Daily_Enhanced" NU EXISTĂ
    echo.
    echo 📋 Pentru a crea task-ul:
    echo 1. Click dreapta pe PowerShell > Run as Administrator
    echo 2. Navighează la directorul cu scripturile
    echo 3. Rulează: .\Create_Arcanum_Scheduled_Task.ps1
    echo.
    goto :end
)

echo.
echo [%date% %time%] Verificare fișiere de stare...
echo ----------------------------------------------------------------------------

REM Verifică fișierele de stare
if exist "state.json" (
    echo ✅ state.json există
    for /f "tokens=2 delims=:" %%a in ('findstr /C:"count" "state.json"') do (
        set "count=%%a"
        set "count=!count:,=!"
        set "count=!count: =!"
        echo 📊 Issue-uri complete: !count!
    )
) else (
    echo ❌ state.json NU există
)

if exist "skip_urls.json" (
    echo ✅ skip_urls.json există
) else (
    echo ❌ skip_urls.json NU există
)

echo.
echo [%date% %time%] Verificare director log-uri...
echo ----------------------------------------------------------------------------

REM Verifică directorul de log-uri
if exist "Logs" (
    echo ✅ Directorul Logs există
    
    REM Găsește cel mai recent log
    set "latest_log="
    for /f "delims=" %%f in ('dir "Logs\arcanum_*.log" /b /o-d 2^>nul') do (
        if not defined latest_log set "latest_log=%%f"
    )
    
    if defined latest_log (
        echo 📄 Ultimul log: !latest_log!
        
        REM Afișează ultimele linii din log
        echo.
        echo [%date% %time%] Ultimele 5 linii din log:
        echo ----------------------------------------------------------------------------
        type "Logs\!latest_log!" | tail -5 2>nul
        if %errorlevel% neq 0 (
            echo (Nu se pot afișa ultimele linii - log-ul poate fi gol)
        )
        echo ----------------------------------------------------------------------------
    ) else (
        echo ℹ️ Nu există log-uri încă
    )
) else (
    echo ❌ Directorul Logs NU există
)

echo.
echo [%date% %time%] Verificare acces la D:\...
echo ----------------------------------------------------------------------------

REM Verifică accesul la D:\
if exist "D:\" (
    echo ✅ Acces la D:\ confirmat
    
    REM Numără fișierele PDF
    set "pdf_count=0"
    for %%f in (D:\*.pdf) do set /a pdf_count+=1
    echo 📄 Fișiere PDF pe D:\: %pdf_count%
    
    if %pdf_count% gtr 0 (
        echo.
        echo [%date% %time%] Ultimele 3 fișiere PDF:
        echo ----------------------------------------------------------------------------
        dir D:\*.pdf /o-d | findstr /C:".pdf" | head -3
        echo ----------------------------------------------------------------------------
    )
) else (
    echo ❌ Nu se poate accesa D:\
)

echo.
echo [%date% %time%] ============================================================================
echo [%date% %time%] REZULTAT VERIFICARE STATUS
echo [%date% %time%] ============================================================================

REM Verifică dacă task-ul este activ
schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /fo list | findstr /i "State.*Ready" >nul
if %errorlevel% equ 0 (
    echo 🟢 STATUS: Task-ul este ACTIV și gata să ruleze
    echo 📅 Va rula automat mâine la 9:00 AM
    echo ✅ Automatizarea funcționează corect
) else (
    schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /fo list | findstr /i "State.*Running" >nul
    if %errorlevel% equ 0 (
        echo 🟡 STATUS: Task-ul rulează ÎN PREZENT
        echo ⏳ Va continua până la finalizare
        echo ✅ Automatizarea este activă
    ) else (
        echo 🔴 STATUS: Task-ul NU este activ
        echo ⚠️ Verifică Task Scheduler pentru detalii
        echo 🔧 Poate fi nevoie să-l activezi manual
    )
)

echo.
echo 📋 OPȚIUNI RAPIDE:
echo 1. Pentru a porni task-ul acum: schtasks /run /tn "Arcanum_PDF_Downloader_Daily_Enhanced"
echo 2. Pentru a opri task-ul: schtasks /end /tn "Arcanum_PDF_Downloader_Daily_Enhanced"
echo 3. Pentru a dezactiva task-ul: schtasks /change /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /disable
echo 4. Pentru a activa task-ul: schtasks /change /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /enable

:end
echo.
echo ============================================================================
echo [%date% %time%] VERIFICARE COMPLETĂ
echo ============================================================================
pause
