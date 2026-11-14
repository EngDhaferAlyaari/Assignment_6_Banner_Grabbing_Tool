@echo off
cd /d "%~dp0"
set /p HOST=Enter your authorized target IP or hostname: 
set /p PORTS=Enter ports (example 21,22,80): 
if exist "Banner_Grabber.exe" (
    "Banner_Grabber.exe" "%HOST%" "%PORTS%"
) else (
    python banner_grabber.py "%HOST%" "%PORTS%"
)
pause
