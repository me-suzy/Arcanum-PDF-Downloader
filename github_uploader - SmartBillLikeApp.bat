@echo off
title SmartBill GitHub Uploader
color 0A

echo ========================================
echo 💰 SMARTBILL GITHUB UPLOADER
echo ========================================
echo.
echo 🚀 Se pregătește upload-ul pe GitHub...
echo.

REM Verifică dacă Python este instalat
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nu este instalat!
    echo Descarcă Python de la: https://python.org
    pause
    exit /b 1
)

REM Instalează dependențele necesare
echo 📦 Instalez dependențele necesare...
pip install -r upload_requirements.txt

if %errorlevel% neq 0 (
    echo ⚠ Instalez PyGithub direct...
    pip install PyGithub requests
)

echo.
echo ✅ Dependențe instalate cu succes!
echo.
echo 🔑 Vei fi întrebat să introduci:
echo    - Username-ul tău GitHub
echo    - Token-ul GitHub (pentru autentificare)
echo.
echo 💡 Pentru token GitHub:
echo    1. Mergi la: https://github.com/settings/tokens
echo    2. Generate new token (classic)
echo    3. Selectează: repo (full control)
echo    4. Copiază token-ul generat
echo.
pause

REM Rulează script-ul Python
python github_uploader.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Upload completat cu succes!
    echo 💰 SmartBill este acum pe GitHub!
) else (
    echo.
    echo ❌ Upload eșuat! Verifică erorile de mai sus.
)

echo.
pause
