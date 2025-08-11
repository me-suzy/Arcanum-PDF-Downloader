@echo off
echo ========================================
echo UPDATE TASK SCHEDULER - ULTRA SIMPLU
echo ========================================
echo.
echo Acest script va actualiza task-ul sa foloseasca
echo run_python_direct.bat care FUNCTIONEAZA perfect!
echo.
pause

echo.
echo Schimb la directorul corect...
cd /d "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"

echo Directorul curent: %cd%
echo.

echo Verific fisierul run_python_direct.bat...
if exist "run_python_direct.bat" (
    echo [OK] run_python_direct.bat gasit!
) else (
    echo [ERROR] run_python_direct.bat NU gasit!
    echo.
    pause
    exit
)

echo.
echo Sterg task-ul vechi...
schtasks /delete /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /f
echo.

echo Creez task-ul nou cu run_python_direct.bat...
echo.
schtasks /create ^
    /tn "Arcanum_PDF_Downloader_Daily_Enhanced" ^
    /tr "cmd.exe /c \"%cd%\run_python_direct.bat\"" ^
    /sc daily ^
    /st 09:00 ^
    /ru "%USERNAME%" ^
    /f

echo.
if %errorlevel% equ 0 (
    echo ========================================
    echo SUCCESS! TASK-UL A FOST CREAT!
    echo ========================================
    echo.
    echo INFORMATII TASK:
    echo - Nume: Arcanum_PDF_Downloader_Daily_Enhanced  
    echo - Frecventa: ZILNIC la 9:00 AM
    echo - Foloseste: run_python_direct.bat
    echo - Directorul: %cd%
    echo.
    echo PROGRAMARE:
    echo - Maine dimineata la 9:00 AM va porni automat
    echo - In fiecare zi la 9:00 AM va rula din nou
    echo - Va continua issue-ul partial din 1969
    echo.
) else (
    echo ========================================  
    echo EROARE LA CREARE TASK!
    echo ========================================
    echo Cod eroare: %errorlevel%
    echo.
)

echo Verific task-ul creat...
echo.
schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /fo table

echo.
echo ========================================
echo TESTARE OPTIONALA
echo ========================================
set /p test="Doresti sa testezi task-ul ACUM? (y/n): "
if /i "%test%"=="y" (
    echo.
    echo Pornesc task-ul pentru test...
    schtasks /run /tn "Arcanum_PDF_Downloader_Daily_Enhanced"
    echo.
    echo Daca a functionat, ar trebui sa se deschida o fereastra
    echo cu command prompt si scriptul Python!
    echo.
)

echo ========================================
echo FINALIZAT!  
echo ========================================
echo.
echo Task-ul este configurat sa ruleze ZILNIC la 9:00 AM
echo Foloseste run_python_direct.bat care FUNCTIONEAZA!
echo.
echo Pentru a verifica statusul:
echo schtasks /query /tn "Arcanum_PDF_Downloader_Daily_Enhanced"
echo.
echo Pentru a opri task-ul:
echo schtasks /delete /tn "Arcanum_PDF_Downloader_Daily_Enhanced" /f
echo.
echo.
echo ========================================
echo SCRIPTUL S-A TERMINAT - FEREASTRA RAMANE DESCHISA
echo ========================================
echo.
pause
echo.
echo Ultima pauza...
pause
echo.
echo Gata! Poti inchide fereastra acum.