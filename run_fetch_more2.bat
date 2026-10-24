@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Downloading irrigation polygons and census tables - keep this window open...
python -u scripts\fetch_more2.py > fetch_more2_log.txt 2>&1
echo Done.
timeout /t 10
