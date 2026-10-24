@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
set LOG=%~dp0smoke_log.txt
echo === update and test %date% %time% === > "%LOG%"
call .venv\Scripts\activate.bat
echo [1/3] Downloading 2019 rain (ERA5)...
python scripts\download_data.py --only D10 --era5-years 2018 2019 >> "%LOG%" 2>&1
echo --- download exit %errorlevel% --- >> "%LOG%"
echo [2/3] Rebuilding clean data...
python scripts\build_clean_data.py >> "%LOG%" 2>&1
echo --- build exit %errorlevel% --- >> "%LOG%"
echo [3/3] Smoke-testing every tab...
python scripts\smoke_test.py >> "%LOG%" 2>&1
echo --- smoke exit %errorlevel% --- >> "%LOG%"
echo Done. See smoke_log.txt
timeout /t 15
