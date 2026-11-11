@echo off
chcp 65001 > nul
echo 正在启动 AL 自学系统 (含旧进程清理 + 绝对路径)...
REM 清理旧 python 8000 进程，防多实例冲突
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID:"') do (
  taskkill /PID %%a /F 2>nul
)
REM 使用本目录下 python，避免系统路径写死问题
set "PY=%~dp0python" 
if exist "%PY%.exe" (
  "%PY%.exe" server.py
) else if exist "%~dp0.\tools\python.exe" (
  "%~dp0.\tools\python.exe" server.py
) else (
  python server.py
)
pause
