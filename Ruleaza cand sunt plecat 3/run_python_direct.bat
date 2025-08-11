@echo off
REM ============================================================================
REM Script SIMPLIFICAT pentru rularea directă a Python-ului zilnic
REM FĂRĂ complicații - doar rulează scriptul Python direct
REM ============================================================================

echo [%date% %time%] PORNIRE AUTOMATA PYTHON ARCANUM
echo ============================================================================

REM Setează directorul de lucru (CALEA TA EXACTĂ)
cd /d "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"

echo Directorul curent: %cd%
echo.

REM Verifică dacă scriptul Python există
if not exist "Claude-FINAL 2 - BUN Sterge pdf pe D.py" (
    echo EROARE: Nu găsesc scriptul Python!
    echo Caut: "Claude-FINAL 2 - BUN Sterge pdf pe D.py"
    echo În directorul: %cd%
    echo.
    echo Task-ul va încerca din nou mâine la 9:00 AM
    pause
    exit /b 1
)

echo Script Python găsit: "Claude-FINAL 2 - BUN Sterge pdf pe D.py"
echo.

REM Resetează flag-ul de limită zilnică (dacă există scriptul)
if exist "reset_daily_limit.py" (
    echo Resetez flag-ul de limită zilnică...
    py "reset_daily_limit.py"
    echo.
)

REM RULEAZĂ DIRECT SCRIPTUL PYTHON
echo ============================================================================
echo PORNESC SCRIPTUL PYTHON PRINCIPAL...
echo ============================================================================
echo.

REM Încearcă py (Python Launcher pentru Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Folosesc comanda: py
    echo Pornesc: py "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated
    echo.
    py "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated
    goto :finished
)

REM Încearcă python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Folosesc comanda: python3
    echo Pornesc: python3 "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated
    echo.
    python3 "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated
    goto :finished
)

REM Încearcă python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Folosesc comanda: python
    echo Pornesc: python "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated
    echo.
    python "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated
    goto :finished
)

REM Dacă nimic nu funcționează
echo EROARE: Nu am găsit nicio comandă Python funcțională!
echo Verifică că Python este instalat și în PATH
echo.
exit /b 1

:finished
echo.
echo ============================================================================
echo SCRIPT PYTHON TERMINAT
echo ============================================================================
echo Cod de ieșire: %errorlevel%
echo Data/Ora terminare: %date% %time%
echo.
echo Task-ul va rula din nou mâine la 9:00 AM
echo.

REM ÎNTOTDEAUNA returnează cod de succes pentru Task Scheduler
REM astfel task-ul va continua să ruleze zilnic
exit /b 0