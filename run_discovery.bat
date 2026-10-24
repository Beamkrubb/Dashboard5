@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Searching open-data portals - keep this window open...
python -u scripts\discover_open_data.py > discover_log.txt 2>&1
echo Done.
timeout /t 10
