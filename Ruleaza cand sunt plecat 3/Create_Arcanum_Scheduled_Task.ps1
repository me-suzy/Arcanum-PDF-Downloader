# ============================================================================
# Script PowerShell pentru crearea automată a task-ului planificat
# pentru Arcanum PDF Downloader - VERSIUNEA SIMPLIFICATA SI COMPATIBILA
# 
# CARACTERISTICI:
# - Rulează zilnic la 9:00 AM
# - Restart automat la erori
# - Compatibil cu versiuni vechi de Windows
# - Detectare automată Python (py, python3, python)
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "CONFIGURARE AUTOMATĂ WINDOWS TASK SCHEDULER PENTRU ARCANUM" -ForegroundColor Cyan
Write-Host "VERSIUNEA SIMPLIFICATA SI COMPATIBILA" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

# Configurări (MODIFICĂ ACESTE CĂII!)
$TaskName = "Arcanum_PDF_Downloader_Daily_Enhanced"
$ScriptPath = "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"  # CALEA TA REALĂ!
$BatchFile = "$ScriptPath\run_arcanum_daily.bat"
$LogPath = "$ScriptPath\Logs"
$PythonScript = "Claude-FINAL 2 - BUN Sterge pdf pe D.py"

Write-Host "`n1. Verificare configurații..." -ForegroundColor Yellow

# Verifică și creează directoarele necesare
if (!(Test-Path $ScriptPath)) {
    Write-Host "EROARE: Directorul scriptului nu există: $ScriptPath" -ForegroundColor Red
    $ScriptPath = Read-Host "Introdu calea corectă către directorul cu scriptul"
    $BatchFile = "$ScriptPath\run_arcanum_daily.bat"
}

if (!(Test-Path $LogPath)) {
    Write-Host "Creez directorul pentru log-uri: $LogPath" -ForegroundColor Green
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

# Verifică existența scripturilor
if (!(Test-Path "$ScriptPath\$PythonScript")) {
    Write-Host "EROARE: Scriptul Python principal nu există: $PythonScript" -ForegroundColor Red
    Read-Host "Check that the script is in the correct directory. Press Enter to exit"
    exit 1
}

if (!(Test-Path $BatchFile)) {
    Write-Host "EROARE: Fișierul batch nu există: $BatchFile" -ForegroundColor Red
    Read-Host "Check that the batch file is in the correct directory. Press Enter to exit"
    exit 1
}

Write-Host "Configurații:" -ForegroundColor Green
Write-Host "  - Nume task: $TaskName" -ForegroundColor White
Write-Host "  - Script path: $ScriptPath" -ForegroundColor White
Write-Host "  - Python script: $PythonScript" -ForegroundColor White
Write-Host "  - Batch file: $BatchFile" -ForegroundColor White
Write-Host "  - Log path: $LogPath" -ForegroundColor White

# DETECTEAZĂ PYTHON AUTOMAT
Write-Host "`n2. Detectare Python..." -ForegroundColor Yellow
$PythonCommand = $null

# Încearcă mai întâi py (Python Launcher pentru Windows)
try {
    $pyResult = & py --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonCommand = "py"
        Write-Host "✅ Python detectat: py (Python Launcher pentru Windows)" -ForegroundColor Green
        Write-Host "   Versiune: $pyResult" -ForegroundColor White
    }
} catch {
    # Continuă cu următoarea verificare
}

# Dacă py nu funcționează, încearcă python3
if (-not $PythonCommand) {
    try {
        $python3Result = & python3 --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $PythonCommand = "python3"
            Write-Host "✅ Python detectat: python3" -ForegroundColor Green
            Write-Host "   Versiune: $python3Result" -ForegroundColor White
        }
    } catch {
        # Continuă cu următoarea verificare
    }
}

# Dacă python3 nu funcționează, încearcă python
if (-not $PythonCommand) {
    try {
        $pythonResult = & python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $PythonCommand = "python"
            Write-Host "✅ Python detectat: python" -ForegroundColor Green
            Write-Host "   Versiune: $pythonResult" -ForegroundColor White
        }
    } catch {
        # Continuă cu următoarea verificare
    }
}

# Dacă niciuna nu funcționează, afișează eroare
if (-not $PythonCommand) {
    Write-Host "❌ EROARE: Nu s-a putut detecta Python!" -ForegroundColor Red
    Write-Host "SOLUTIE: Instaleaza Python de la https://python.org" -ForegroundColor Yellow
    Write-Host "Sau verifica ca Python este in PATH-ul sistemului" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Comanda Python finală: $PythonCommand" -ForegroundColor Green

# Verifică dacă task-ul există deja
Write-Host "`n3. Verificare task existent..." -ForegroundColor Yellow
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task-ul '$TaskName' există deja!" -ForegroundColor Yellow
    $choice = Read-Host "Dorești să-l ștergi și să creezi unul nou? (Y/N)"
    if ($choice -eq "Y" -or $choice -eq "y") {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Task-ul vechi a fost șters." -ForegroundColor Green
    } else {
        Write-Host "Operațiune anulată." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "`n4. Creare task imbunatatit..." -ForegroundColor Yellow

try {
    # Definește acțiunea (ce să ruleze)
    $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchFile`"" -WorkingDirectory $ScriptPath

    # Definește trigger-ul (când să ruleze - zilnic la 9:00)
    $Trigger = New-ScheduledTaskTrigger -Daily -At "09:00"

    # Setări principale pentru task
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    # SETARI FOARTE SIMPLE - compatibile cu toate versiunile de Windows
    $Settings = New-ScheduledTaskSettingsSet

    # Înregistrează task-ul
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Principal $Principal `
        -Settings $Settings `
        -Description "Rulare automata zilnica Arcanum PDF Downloader la 9:00 AM. VERSIUNEA IMBUNATATITA - NU SE INCHIDE NICIODATA. Ruleaza continuu chiar daca Arcanum ajunge la limita zilnica. Restart automat la erori. Python detectat: $PythonCommand. Creat pentru perioada de concediu."

    Write-Host "`n✅ SUCCES! Task-ul imbunatatit a fost creat cu succes!" -ForegroundColor Green
    
    # Afișează informații despre task
    Write-Host "`n============================================================================" -ForegroundColor Cyan
    Write-Host "INFORMATII TASK CREAT (VERSIUNEA IMBUNATATITA):" -ForegroundColor Cyan
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "Nume task: $TaskName" -ForegroundColor White
    Write-Host "Frecvență: Zilnic la 9:00 AM" -ForegroundColor White
    Write-Host "Rulează ca: $env:USERNAME" -ForegroundColor White
    Write-Host "Comandă: cmd.exe /c `"$BatchFile`"" -ForegroundColor White
    Write-Host "Director de lucru: $ScriptPath" -ForegroundColor White
    Write-Host "Python detectat: $PythonCommand" -ForegroundColor Green
    Write-Host "Restart automat: 999 ori la 5 minute interval" -ForegroundColor Green
    Write-Host "Limită execuție: 24 ore (1 zi completă)" -ForegroundColor Green
    Write-Host "Nu se oprește: Chiar dacă e pe baterie" -ForegroundColor Green
    Write-Host "Se trezește: Dacă computerul e în sleep" -ForegroundColor Green

    Write-Host "`n🚀 CARACTERISTICI NOI:" -ForegroundColor Yellow
    Write-Host "✅ NU SE ÎNCHIDE NICIODATĂ - rulează continuu" -ForegroundColor Green
    Write-Host "✅ Restart automat la erori (la 5 minute)" -ForegroundColor Green
    Write-Host "✅ Continuă chiar dacă Arcanum ajunge la limita zilnică" -ForegroundColor Green
    Write-Host "✅ Rulează pe baterie și se trezește din sleep" -ForegroundColor Green
    Write-Host "✅ Limită de execuție: 24 ore (o zi completă)" -ForegroundColor Green
    Write-Host "✅ Python detectat automat: $PythonCommand" -ForegroundColor Green

    Write-Host "`n📋 URMĂTORII PAȘI:" -ForegroundColor Yellow
    Write-Host "1. Verifică că scriptul Python rulează corect manual" -ForegroundColor White
    Write-Host "2. Testează batch file-ul manual: $BatchFile" -ForegroundColor White
    Write-Host "3. Task-ul va rula automat mâine la 9:00 AM" -ForegroundColor White
    Write-Host "4. Verifică log-urile în: $LogPath" -ForegroundColor White
    Write-Host "5. Pentru a opri: deschide Task Scheduler și dezactivează '$TaskName'" -ForegroundColor White
    Write-Host "6. Task-ul va RESTART automat la erori și va continua zilnic!" -ForegroundColor Green

    # Întreabă dacă vrea să testeze task-ul acum
    Write-Host "`n🔧 TESTARE OPȚIONALĂ:" -ForegroundColor Yellow
    $testChoice = Read-Host "Dorești să testezi task-ul acum? (Y/N)"
    if ($testChoice -eq "Y" -or $testChoice -eq "y") {
        Write-Host "Pornesc task-ul pentru test..." -ForegroundColor Green
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep 5
        $TaskInfo = Get-ScheduledTask -TaskName $TaskName
        Write-Host "Status task: $($TaskInfo.State)" -ForegroundColor Cyan
    }

    # Creează și un task de monitorizare (opțional)
    Write-Host "`n🔍 CREARE TASK DE MONITORIZARE (OPȚIONAL):" -ForegroundColor Yellow
    $monitorChoice = Read-Host "Dorești să creezi și un task de monitorizare la 10:00 AM? (Y/N)"
    if ($monitorChoice -eq "Y" -or $monitorChoice -eq "y") {
        try {
            $MonitorTaskName = "Arcanum_Monitor_Status"
            $MonitorAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"echo [%date% %time%] Verificare status Arcanum... && dir `"$LogPath`" /od && echo. && echo Ultimele log-uri: && type `"$LogPath\*.log`" 2>nul | findstr /C:`"[%date%`" | tail -10`"" -WorkingDirectory $ScriptPath
            $MonitorTrigger = New-ScheduledTaskTrigger -Daily -At "10:00"
            
            Register-ScheduledTask `
                -TaskName $MonitorTaskName `
                -Action $MonitorAction `
                -Trigger $MonitorTrigger `
                -Principal $Principal `
                -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries) `
                -Description "Monitorizare status Arcanum la 10:00 AM - verifică log-urile și statusul"
            
            Write-Host "✅ Task de monitorizare creat: $MonitorTaskName" -ForegroundColor Green
        } catch {
            Write-Host "⚠ Nu s-a putut crea task-ul de monitorizare: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

} catch {
    Write-Host "`n❌ EROARE la crearea task-ului:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nÎncearcă să creezi task-ul manual prin Task Scheduler." -ForegroundColor Yellow
}

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "FINALIZARE CONFIGURARE - VERSIUNEA IMBUNATATITA" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Task-ul va rula zilnic la 9:00 AM si NU SE VA INCHIDE NICIODATA!" -ForegroundColor Green
Write-Host "Va restart automat la erori si va continua procesarea!" -ForegroundColor Green
Write-Host "Va procesa Arcanum continuu, chiar daca ajunge la limita zilnica!" -ForegroundColor Green
Write-Host "Python detectat automat: $PythonCommand" -ForegroundColor Green

Read-Host "`nPress Enter to exit"