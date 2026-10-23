@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
set LOG=%~dp0run_log.txt
echo === run started %date% %time% === > "%LOG%"

where py >nul 2>&1 && (set PY=py -3) || (set PY=python)
%PY% --version >> "%LOG%" 2>&1 || (echo Python not found - install from python.org >> "%LOG%" & echo Python not found & pause & exit /b 1)

if not exist .venv (
  echo [1/5] Creating virtual environment...
  %PY% -m venv .venv >> "%LOG%" 2>&1
)
call .venv\Scripts\activate.bat

echo [2/5] Installing packages (first run takes a few minutes)...
python -m pip install --upgrade pip >> "%LOG%" 2>&1
echo     (keep this window open)
python -m pip install -r requirements.txt >> "%LOG%" 2>&1
echo --- pip exit %errorlevel% --- >> "%LOG%"

echo [3/5] Downloading open data...
python scripts\download_data.py --era5-2018 >> "%LOG%" 2>&1
echo --- download exit %errorlevel% --- >> "%LOG%"

echo [4/5] Building clean data...
python scripts\build_clean_data.py >> "%LOG%" 2>&1
echo --- build exit %errorlevel% --- >> "%LOG%"

echo [5/5] Starting dashboard: open http://127.0.0.1:8050/ in your browser
echo --- streamlit start --- >> "%LOG%"
start "" http://127.0.0.1:8050/
python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8050 >> "%LOG%" 2>&1
echo --- streamlit exit %errorlevel% --- >> "%LOG%"
echo Done. See run_log.txt
pause
