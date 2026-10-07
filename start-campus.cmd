@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m campus.server
) else (
  python -m campus.server
)
pause
