@echo off
echo ========================================
echo TEST RULARE DIRECTA PYTHON
echo ========================================
echo.
echo Testez dacă scriptul Python poate fi rulat direct.
echo Această fereastră NU se va închide automat.
echo.
echo Apasă orice tastă pentru a începe testul...
pause >nul

echo.
echo Step 1: Schimb directorul...
cd /d "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"

if %errorlevel% equ 0 (
    echo [SUCCESS] Directorul schimbat cu succes
    echo Directorul curent: %cd%
) else (
    echo [ERROR] Nu pot schimba directorul
    echo Cod eroare: %errorlevel%
    goto :end
)

echo.
echo Step 2: Verific fișierele necesare...
echo.

if exist "Claude-FINAL 2 - BUN Sterge pdf pe D.py" (
    echo [OK] Scriptul Python principal există
) else (
    echo [ERROR] Scriptul Python principal NU există
    echo Căutam: "Claude-FINAL 2 - BUN Sterge pdf pe D.py"
    goto :end
)

if exist "reset_daily_limit.py" (
    echo [OK] Scriptul de resetare există
) else (
    echo [WARNING] Scriptul de resetare NU există (opțional)
)

if exist "run_python_direct.bat" (
    echo [OK] Batch file-ul direct există
) else (
    echo [WARNING] Batch file-ul direct NU există încă
    echo Trebuie să salvezi run_python_direct.bat în acest director
)

echo.
echo Step 3: Testez comenzile Python...
echo.

echo Testez comanda 'py'...
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 'py' funcționează
    py --version
    set "PYTHON_CMD=py"
    goto :python_found
)

echo Testez comanda 'python3'...
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 'python3' funcționează
    python3 --version
    set "PYTHON_CMD=python3"
    goto :python_found
)

echo Testez comanda 'python'...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 'python' funcționează
    python --version
    set "PYTHON_CMD=python"
    goto :python_found
)

echo [ERROR] Nicio comandă Python nu funcționează!
echo Verifică că Python este instalat și în PATH
goto :end

:python_found
echo.
echo [SUCCESS] Comanda Python găsită: %PYTHON_CMD%

echo.
echo Step 4: Test rulare script resetare (dacă există)...
echo.

if exist "reset_daily_limit.py" (
    echo Rulez: %PYTHON_CMD% reset_daily_limit.py
    %PYTHON_CMD% "reset_daily_limit.py"
    echo Cod ieșire resetare: %errorlevel%
) else (
    echo Sar peste resetarea - fișierul nu există
)

echo.
echo Step 5: Test informații script principal...
echo.

echo Verific dacă scriptul Python poate fi citit...
%PYTHON_CMD% -c "with open('Claude-FINAL 2 - BUN Sterge pdf pe D.py', 'r', encoding='utf-8') as f: print('Script length:', len(f.read()), 'characters')" 2>nul
if %errorlevel% equ 0 (
    echo [OK] Scriptul Python poate fi citit
) else (
    echo [WARNING] Probleme la citirea scriptului Python
)

echo.
echo Step 6: Test importuri Python...
echo.

echo Testez importurile necesare...
%PYTHON_CMD% -c "import selenium, time, os, json; print('Toate importurile funcționează!')" 2>nul
if %errorlevel% equ 0 (
    echo [OK] Toate importurile Python funcționează
) else (
    echo [WARNING] Lipsesc unele module Python (probabil selenium)
    echo Pentru instalare: pip install selenium
)

echo.
echo ========================================
echo REZULTATE TEST
echo ========================================
echo.
echo Python command: %PYTHON_CMD%
echo Working directory: %cd%
echo.

if exist "Claude-FINAL 2 - BUN Sterge pdf pe D.py" (
    if defined PYTHON_CMD (
        echo [SUCCESS] Toate condițiile de bază sunt îndeplinite!
        echo.
        echo URMĂTORII PAȘI:
        echo 1. Salvează run_python_direct.bat în acest director
        echo 2. Rulează Update_Task_Direct_Python.ps1 ca Administrator
        echo 3. Task-ul va rula automat zilnic la 9:00 AM
        echo.
        echo Pentru test manual, rulează:
        echo %PYTHON_CMD% "Claude-FINAL 2 - BUN Sterge pdf pe D.py" --automated
    ) else (
        echo [ERROR] Python nu este configurat corect
    )
) else (
    echo [ERROR] Scriptul Python principal lipsește
)

:end
echo.
echo ========================================
echo TEST FINALIZAT
echo ========================================
echo.
echo Această fereastră va rămâne deschisă.
echo Apasă orice tastă pentru a închide...
pause >nul