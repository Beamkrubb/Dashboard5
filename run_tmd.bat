@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo TMD API: ใส่ uid และ ukey ที่ได้จากการลงทะเบียนที่ data.tmd.go.th (ไม่ถูกบันทึกลงไฟล์)
set /p TMD_UID=uid: 
set /p TMD_UKEY=ukey: 
python -u scripts\download_data.py --only D09
echo Done. ไฟล์อยู่ในโฟลเดอร์ data\cache
pause
