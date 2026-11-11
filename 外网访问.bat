@echo off
chcp 65001 >nul
cd /d "D:\我的作品\自学系统\AL-Learning-System"

echo ===================================================
echo   AL 自学系统 · 外网访问启动器（免费隧道）
echo ===================================================
echo.

REM 1) 启动本地服务（若 8000 端口未被占用）
netstat -ano | findstr /C:":8000 " >nul
if errorlevel 1 (
  echo [1/2] 本地服务未运行，正在启动...
  start "AL学习系统服务" /min "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" server.py
  timeout /t 4 >nul
) else (
  echo [1/2] 本地服务已在运行（端口 8000）。
)

REM 2) 建立免费外网隧道（localhost.run 匿名，完全免费、无需域名）
REM    免费版分配随机子域名，形如 https://xxxx.lhr.life，每次启动地址会变化。
REM    —— 想要固定不变的地址（alstudy.lhr.life）：
REM       需 localhost.run 付费订阅（$9/月）。订阅后在 admin.localhost.run 添加自定义域名，
REM       再把下面一行改成： -R alstudy.lhr.life:80:localhost:8000 localhost.run
echo [2/2] 正在建立外网隧道，请勿关闭此窗口...
echo        稍等几秒，下方会出现形如  https://xxxx.lhr.life  的公网地址
echo        用手机/平板浏览器打开该地址即可访问本机 AL 自学系统。
echo.
C:\Windows\System32\OpenSSH\ssh.exe -i "tools\id_ed25519_lhr" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R 80:localhost:8000 localhost.run

echo.
echo 隧道已断开。如需重新访问，请再次双击本文件。
pause
