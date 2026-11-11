@echo off
chcp 65001 >nul
REM ============================================================
REM  Cloudflare 首次配置（只需运行一次）
REM  作用：登录 Cloudflare 免费账号 + 创建永久隧道 alstudy
REM  完成后会生成一个配置文件，以后用「外网访问-Cloudflare.bat」启动
REM  前置：先把 cloudflared.exe 放到本目录的 tools\ 下，
REM        或在本机用 winget install cloudflare.cloudflared 安装
REM ============================================================
cd /d "%~dp0"

REM 定位 cloudflared
where cloudflared >nul 2>nul && set CF=cloudflared || set "CF=%~dp0tools\cloudflared.exe"
if not exist "%CF%" (
  echo [错误] 找不到 cloudflared.exe！
  echo 请二选一：
  echo   1) 下载 https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe 放到 tools\cloudflared.exe
  echo   2) 在本机命令行运行：winget install cloudflare.cloudflared
  pause & exit /b 1
)

echo.
echo ===== 第1步：登录 Cloudflare（会自动打开浏览器，用邮箱注册/登录，免费）=====
%CF% login

echo.
echo ===== 第2步：创建永久隧道 alstudy（免费，得到 https://alstudy.cfargotunnel.com）=====
%CF% tunnel create alstudy

echo.
echo ===== 第3步：生成本地配置文件 =====
REM 找到刚写入的 credentials 文件（最新的 .json）
set "CRED="
for /f "delims=" %%f in ('dir /b /o-d "%USERPROFILE%\.cloudflared\*.json" 2^>nul') do (
  if not defined CRED set "CRED=%USERPROFILE%\.cloudflared\%%f"
)
if not defined CRED (
  echo [警告] 未找到 credentials 文件，请确认上一步是否成功。
  pause & exit /b 1
)
REM 反斜杠转正斜杠，写进 YAML
set "CRED_YAML=%CRED:\=/%"

> "%~dp0tools\cloudflared-config.yml" (
  echo tunnel: alstudy
  echo credentials-file: %CRED_YAML%
  echo ingress:
  echo   - hostname: alstudy.cfargotunnel.com
  echo     service: http://localhost:8000
  echo   - service: http_status:404
)

echo.
echo [完成] 配置文件已生成：tools\cloudflared-config.yml
echo 你的永久访问地址是： https://alstudy.cfargotunnel.com
echo 以后每天只要双击「外网访问-Cloudflare.bat」即可。
pause
