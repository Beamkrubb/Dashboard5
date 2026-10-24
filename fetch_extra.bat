@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
set LOG=%~dp0fetch_log.txt
echo === fetch extra %date% %time% === > "%LOG%"
call .venv\Scripts\activate.bat
echo Fetching extra real data (about 10 minutes) - keep this window open...
python -u scripts\fetch_extra.py >> "%LOG%" 2>&1
echo --- fetch exit %errorlevel% --- >> "%LOG%"
echo Done. See fetch_log.txt
timeout /t 10
