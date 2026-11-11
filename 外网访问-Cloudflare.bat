@echo off
chcp 65001 >nul
REM ============================================================
REM  外网访问启动器（每天用）
REM  启动本地服务 + 拉起 Cloudflare 永久隧道
REM  手机/平板在任何网络用浏览器打开： https://alstudy.cfargotunnel.com
REM ============================================================
cd /d "%~dp0"

REM 定位 cloudflared
where cloudflared >nul 2>nul && set CF=cloudflared || set "CF=%~dp0tools\cloudflared.exe"
if not exist "%CF%" (
  echo [错误] 找不到 cloudflared.exe，请先运行「Cloudflare首次配置.bat」。
  pause & exit /b 1
)
if not exist "%~dp0tools\cloudflared-config.yml" (
  echo [错误] 找不到配置文件，请先运行「Cloudflare首次配置.bat」。
  pause & exit /b 1
)

REM 若本地服务未启动，则启动（用沙箱托管的 python）
set "PY=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
netstat -ano 2>nul | find ":8000" >nul 2>nul || (
  echo 启动本地学习系统服务...
  start "" "%PY%" server.py
  timeout /t 3 >nul
)

echo.
echo 正在拉起 Cloudflare 永久隧道： https://alstudy.cfargotunnel.com
echo （关闭本窗口即停止外网访问；本地服务仍在后台运行）
echo.
%CF% tunnel run --config "%~dp0tools\cloudflared-config.yml" alstudy
pause
