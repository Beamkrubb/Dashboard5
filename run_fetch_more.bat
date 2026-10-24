@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Downloading more open data - keep this window open...
python -u scripts\fetch_more.py > fetch_more_log.txt 2>&1
echo Done.
timeout /t 10
