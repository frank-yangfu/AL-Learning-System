@echo off
chcp 65001 >nul
echo =====================================================
echo   AL 自学系统 · 花生壳外网访问启动器 (免费版)
echo =====================================================
echo.
REM ---------- 清旧进程，防 8000 端口被旧 server 占用 ----------
echo [清理] 检查旧 server / cpolar / 花生壳进程...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID:"') do (
  echo    杀掉旧 python.exe PID %%a (若占用 8000)
  taskkill /PID %%a /F 2>nul
)
echo [清理] 完成。

echo [1/4] 启动 AL 自学系统服务 (端口 8000)...
set "PY=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
start "AL学习系统服务" /min "%PY%" "D:\我的作品\自学系统\AL-Learning-System\server.py"
timeout /t 3 >nul

echo [2/4] 检查端口 8000 是否监听...
netstat -ano 2>nul | findstr ":8000" >nul
if errorlevel 1 (
  echo [警告] 服务未在 3 秒内启动，可能端口被占用或 python 路径错误。
) else (
  echo [OK] 本地服务已运行 (http://localhost:8000)
)

echo [3/4] 请先手动打开花生壳客户端，登录后「内网穿透」添加映射：
echo        内网主机：127.0.0.1  |  端口：8000  |  应用类型：HTTP
echo        外网域名：由花生壳免费分配（如 alstudy.oicp.net，选你喜欢的前缀）
echo [提示] 花生壳免费版：固定域名、1Mbps 带宽、需一次扫码登录，无需付费。

echo [4/4] 待花生壳映射生效后，用浏览器打开：
echo        https://你的前缀.oicp.net   （电脑开机后地址永远不变）
echo.
echo ==========================================
echo   开机自启建议：
echo     1. 花生壳客户端 → 设置 → 开机自启
pause & echo.
echo   2. 本脚本放入「开始菜单 → 启动」文件夹，电脑开机自动执行
echo   （或创建任务计划：延迟 30 秒后运行本 bat）
echo ==========================================
pause
