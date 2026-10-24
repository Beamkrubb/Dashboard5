@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Downloading ERA5 for the remaining provinces - keep this window open...
python -u scripts\fetch_era5_missing.py > fetch_era5_log.txt 2>&1
type fetch_era5_log.txt
timeout /t 15
