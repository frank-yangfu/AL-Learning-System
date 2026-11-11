@echo off
cd /d "%~dp0"
set PORT=8001
start "" "C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\pythonw.exe" server.py
exit
