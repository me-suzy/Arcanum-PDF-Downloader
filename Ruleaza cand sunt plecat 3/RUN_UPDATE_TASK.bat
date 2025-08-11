@echo off
echo ========================================
echo ACTUALIZARE TASK SCHEDULER - METODA SIGURA
echo ========================================
echo.
echo Acest script va actualiza Task Scheduler sa foloseasca
echo run_python_direct.bat care FUNCTIONEAZA.
echo.
echo IMPORTANT: Fereastra va ramane deschisa!
echo.
echo Apasa orice tasta pentru a continua...
pause >nul

echo.
echo Step 1: Verific daca rulez ca Administrator...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo EROARE: NU RULEZI CA ADMINISTRATOR!
    echo ========================================
    echo.
    echo Pentru a rula ca Administrator:
    echo 1. Click dreapta pe acest fisier (RUN_UPDATE_TASK.bat)
    echo 2. Selecteaza "Run as administrator"
    echo 3. Confirma cu "Yes"
    echo.
    echo Apoi ruleaza din nou acest script.
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Rulez ca Administrator - OK!
echo.

echo Step 2: Schimb la directorul corect...
cd /d "%~dp0"
echo Directorul curent: %cd%
echo.

echo Step 3: Verific fisierele necesare...
if not exist "run_python_direct.bat" (
    echo [ERROR] Nu gasesc run_python_direct.bat!
    echo Asigura-te ca ai salvat fisierul in acest director.
    pause
    exit /b 1
)
echo [OK] run_python_direct.bat gasit!

if not exist "Claude-FINAL 2 - BUN Sterge pdf pe D.py" (
    echo [ERROR] Nu gasesc scriptul Python!
    pause
    exit /b 1
)
echo [OK] Scriptul Python gasit!
echo.

echo Step 4: Actualizez Task Scheduler...
echo.
echo Sterg task-ul vechi (daca exista)...
schtasks /delete /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Task-ul vechi sters
) else (
    echo [INFO] Nu exista task vechi de sters
)

echo.
echo Creez task-ul nou cu run_python_direct.bat...
schtasks /create ^
    /tn "Arcanum_PDF_Downloader_Daily_Enhanced" ^
    /tr "cmd.exe /c \"%cd%\run_python_direct.bat\"" ^
    /sc daily ^
    /st 09:00 ^
    /ru "%USERNAME%" ^
    /rl highest ^
    /f

if %errorlevel% equ 0 (
    echo [SUCCESS] Task-ul a fost creat cu succes!
) else (
    echo [ERROR] Eroare la crearea task-ului: %errorlevel%
    pause
    exit /b 1
)

echo.
echo Step 5: Configurez setari avansate...
schtasks /change /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /enable >nul 2>&1
echo [OK] Task activat

echo.
echo Step 6: Verific task-ul creat...
schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /fo list | findstr /C:"Task Name" /C:"Status" /C:"Next Run Time"

echo.
echo ========================================
echo TASK ACTUALIZAT CU SUCCES!
echo ========================================
echo.
echo INFORMATII TASK:
echo - Nume: Arcanum_PDF_Downloader_Daily_Enhanced
echo - Frecventa: ZILNIC la 9:00 AM
echo - Comanda: cmd.exe /c "%cd%\run_python_direct.bat"
echo - Batch file: run_python_direct.bat (cel care FUNCTIONEAZA!)
echo.
echo PROGRAMARE:
echo - Maine dimineata la 9:00 AM task-ul va porni automat
echo - In fiecare zi la 9:00 AM va rula din nou
echo - Va continua cu issue-ul partial (1969) de la pagina 600
echo - Dupa ce termina, va trece la anii lipsa
echo.
echo TESTARE OPTIONALA:
set /p test_choice="Doresti sa testezi task-ul ACUM? (Y/N): "
if /i "%test_choice%"=="Y" (
    echo.
    echo Pornesc task-ul pentru test...
    schtasks /run /tn "Arcanum_PDF_Downloader_Daily_Enhanced"
    if %errorlevel% equ 0 (
        echo [OK] Task-ul a fost pornit!
        echo Verifica daca s-a deschis o fereastra cu scriptul!
    ) else (
        echo [ERROR] Nu am putut porni task-ul pentru test
    )
)

echo.
echo ========================================
echo CONFIGURARE FINALIZATA!
echo ========================================
echo.
echo Task-ul va rula automat ZILNIC la 9:00 AM!
echo Foloseste run_python_direct.bat care FUNCTIONEAZA!
echo Va continua automatizarea in fiecare zi!
echo.
echo Pentru a verifica statusul task-ului, poti rula:
echo schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced"
echo.
echo Apasa orice tasta pentru a inchide...
pause >nul