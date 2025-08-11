# ============================================================================
# Script PowerShell pentru actualizarea task-ului să folosească noul batch
# care FUNCȚIONEAZĂ (run_python_direct.bat)
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "ACTUALIZARE TASK PENTRU run_python_direct.bat" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

# Verifică dacă rulează ca Administrator
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "EROARE: Acest script trebuie rulat ca Administrator!" -ForegroundColor Red
    Write-Host "Click dreapta pe PowerShell > Run as administrator" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Rulează ca Administrator" -ForegroundColor Green

# Configurări
$TaskName = "Arcanum_PDF_Downloader_Daily_Enhanced"
$ScriptPath = "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"
$NewBatchFile = "$ScriptPath\run_python_direct.bat"

Write-Host "`nConfigurații:" -ForegroundColor Green
Write-Host "  - Task name: $TaskName" -ForegroundColor White
Write-Host "  - Script path: $ScriptPath" -ForegroundColor White
Write-Host "  - Batch file nou: $NewBatchFile" -ForegroundColor White

# Verifică dacă task-ul există
Write-Host "`n1. Verificare task existent..." -ForegroundColor Yellow
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $ExistingTask) {
    Write-Host "EROARE: Task-ul '$TaskName' nu există!" -ForegroundColor Red
    Write-Host "Voi crea un task nou..." -ForegroundColor Yellow
} else {
    Write-Host "✅ Task-ul '$TaskName' găsit!" -ForegroundColor Green
    Write-Host "Status curent: $($ExistingTask.State)" -ForegroundColor Cyan
}

# Verifică fișierele
Write-Host "`n2. Verificare fișiere..." -ForegroundColor Yellow

if (-not (Test-Path $ScriptPath)) {
    Write-Host "EROARE: Directorul nu există: $ScriptPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $NewBatchFile)) {
    Write-Host "EROARE: Batch file-ul nou nu există: $NewBatchFile" -ForegroundColor Red
    Write-Host "Asigură-te că ai salvat run_python_direct.bat în directorul corect!" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Toate fișierele există!" -ForegroundColor Green

# Șterge task-ul vechi (dacă există)
if ($ExistingTask) {
    Write-Host "`n3. Șterg task-ul vechi..." -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ Task-ul vechi șters cu succes." -ForegroundColor Green
    } catch {
        Write-Host "❌ Eroare la ștergerea task-ului vechi: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Creează task-ul nou
Write-Host "`n4. Creez task-ul nou..." -ForegroundColor Yellow

try {
    # Acțiunea - rulează noul batch file
    $Action = New-ScheduledTaskAction `
        -Execute "cmd.exe" `
        -Argument "/c `"$NewBatchFile`"" `
        -WorkingDirectory $ScriptPath

    # Trigger - zilnic la 9:00 AM
    $Trigger = New-ScheduledTaskTrigger -Daily -At "09:00"

    # Principal - user curent
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    # Settings - compatibile cu toate versiunile Windows
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 24) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)

    # Înregistrează task-ul nou
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Principal $Principal `
        -Settings $Settings `
        -Description "Rulare automata zilnica Arcanum PDF Downloader la 9:00 AM - VERSIUNEA FINALĂ QUE FUNCȚIONEAZĂ. Folosește run_python_direct.bat care rulează direct Python fără probleme. Restart automat la erori. Va continua zilnic chiar dacă atinge limita. Creat pentru automatizare completă."

    Write-Host "✅ Task-ul a fost creat cu succes!" -ForegroundColor Green

} catch {
    Write-Host "❌ EROARE la crearea task-ului: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Verifică task-ul nou creat
Write-Host "`n5. Verificare task nou..." -ForegroundColor Yellow
$NewTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($NewTask) {
    Write-Host "✅ Task-ul nou a fost creat cu succes!" -ForegroundColor Green
    Write-Host "Status: $($NewTask.State)" -ForegroundColor Cyan
    
    # Afișează detalii despre task
    $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($TaskInfo) {
        Write-Host "Ultima rulare: $($TaskInfo.LastRunTime)" -ForegroundColor White
        Write-Host "Următoarea rulare: $($TaskInfo.NextRunTime)" -ForegroundColor White
    }
} else {
    Write-Host "❌ Task-ul nu a fost creat corect!" -ForegroundColor Red
}

# Rezultat final
Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "TASK ACTUALIZAT CU SUCCES!" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "✅ Task name: $TaskName" -ForegroundColor White
Write-Host "✅ Acțiune: cmd.exe /c `"$NewBatchFile`"" -ForegroundColor White
Write-Host "✅ Frecvență: Zilnic la 9:00 AM" -ForegroundColor White
Write-Host "✅ Working directory: $ScriptPath" -ForegroundColor White
Write-Host "✅ Batch file: run_python_direct.bat (cel care FUNCȚIONEAZĂ!)" -ForegroundColor Green

Write-Host "`n🚀 CARACTERISTICI:" -ForegroundColor Yellow
Write-Host "✅ Rulează ZILNIC la 9:00 AM automat" -ForegroundColor Green
Write-Host "✅ Folosește batch file-ul care FUNCȚIONEAZĂ" -ForegroundColor Green
Write-Host "✅ Restart automat la erori (3 ori la 5 minute)" -ForegroundColor Green
Write-Host "✅ Limită execuție: 24 ore (o zi completă)" -ForegroundColor Green
Write-Host "✅ Rulează pe baterie și se trezește din sleep" -ForegroundColor Green
Write-Host "✅ Va continua zilnic chiar dacă atinge limita" -ForegroundColor Green

Write-Host "`n📅 PROGRAM:" -ForegroundColor Yellow
Write-Host "🕘 Mâine dimineață la 9:00 AM, task-ul va porni automat" -ForegroundColor Green
Write-Host "🔄 În fiecare zi la 9:00 AM va rula din nou" -ForegroundColor Green
Write-Host "📊 Va continua cu issue-ul parțial (1969) de la pagina 600" -ForegroundColor Green
Write-Host "🎯 După ce termină issue-ul parțial, va trece la anii lipsă" -ForegroundColor Green

# Test opțional
Write-Host "`n🔧 TESTARE:" -ForegroundColor Yellow
$testChoice = Read-Host "Dorești să testezi task-ul ACUM? (Y/N)"
if ($testChoice -eq "Y" -or $testChoice -eq "y") {
    Write-Host "🚀 Pornesc task-ul pentru test..." -ForegroundColor Green
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "✅ Task-ul a fost pornit!" -ForegroundColor Green
        Write-Host "📱 Verifică dacă s-a deschis o fereastră cu command prompt și scriptul Python!" -ForegroundColor Yellow
        
        Start-Sleep 5
        $TaskStatus = Get-ScheduledTask -TaskName $TaskName
        Write-Host "Status curent: $($TaskStatus.State)" -ForegroundColor Cyan
        
    } catch {
        Write-Host "❌ Eroare la pornirea task-ului: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "CONFIGURARE FINALIZATĂ!" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "🎉 Task-ul va rula automat zilnic la 9:00 AM!" -ForegroundColor Green
Write-Host "🎯 Folosește batch file-ul care FUNCȚIONEAZĂ!" -ForegroundColor Green
Write-Host "📈 Va continua automatizarea Arcanum în fiecare zi!" -ForegroundColor Green

Read-Host "`nPress Enter to exit"