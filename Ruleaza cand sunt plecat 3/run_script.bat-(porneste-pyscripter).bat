@echo off
cd /d "E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3"
start "" "C:\Program Files\PyScripter\PyScripter.exe" --python312 "Claude-FINAL 3 - BUN Sterge pdf pe D.py"
timeout /t 5 /nobreak >nul
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^{F9}')"