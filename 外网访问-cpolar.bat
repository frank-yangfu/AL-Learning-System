@echo off
REM ================================================================
REM  AL Self-study System - Public access launcher (cpolar)
REM  NOTE: console output is intentionally pure ASCII.
REM ================================================================
chcp 65001 >nul
cd /d "%~dp0"
setlocal enabledelayedexpansion

set "VENV=C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
set "TMPOUT=%TEMP%\al_cpolar_out.txt"

echo.
echo ================================================================
echo   AL Study System - Public Access via cpolar
echo ================================================================
echo.

if not exist "%VENV%" (
    echo [ERROR] venv python not found:
    echo         %VENV%
    echo         Reinstall the isolated venv, then try again.
    pause
    exit /b 1
)

REM ---------------- 1. local service on port 8000 ----------------
echo [1/5] Checking local service on port 8000 ...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo       Not running. Starting with venv python ^(edge-tts enabled^) ...
    start "AL Study Service" /min "%VENV%" "%~dp0server.py"
) else (
    echo       [OK] Already running.
)

set /a TRY=0
:WAITLOOP
timeout /t 1 >nul
set /a TRY+=1
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if errorlevel 1 (
    if !TRY! LSS 25 goto WAITLOOP
    echo       [WARN] Port 8000 not listening after 25s.
    echo       Check server_cpolar.log / run 启动_AL系统_语音版.bat manually.
) else (
    echo       [OK] Local service ready on 127.0.0.1:8000
)

REM ---------------- 2. cpolar service ----------------
echo.
echo [2/5] Checking Cpolar Service ...
net start | findstr /i "Cpolar" >nul
if errorlevel 1 (
    echo       [WARN] Cpolar Service is NOT running.
    echo       Start it: Windows Search -^> Services -^> "Cpolar Service" -^> Start
) else (
    echo       [OK] Cpolar Service is running.
)

REM ---------------- 3. resolve public address ----------------
echo.
echo [3/5] Resolving public address from cpolar log ...
"%VENV%" "%~dp0al_cpolar_url.py" --open > "%TMPOUT%" 2>&1

set "PUBURL="
for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "URL=" "%TMPOUT%"`) do set "PUBURL=%%b"

if not defined PUBURL (
    echo       [ERROR] No tunnel pointing to port 8000 was found.
    echo.
    echo       Fix it in cpolar web UI:
    echo         1. Open  http://localhost:9200
    echo         2. Delete an unused tunnel  ^(free plan has a tunnel limit^)
    echo         3. Create a tunnel -^> Local address: 8000, protocol: http+https
    echo         4. Run this bat again
    echo.
    type "%TMPOUT%"
    pause
    exit /b 1
)

REM ---------------- 4. clipboard ----------------
echo       [OK] Tunnel found.
echo.
echo [4/5] Copying address to clipboard ...
echo|set /p="%PUBURL%" | clip
echo       [OK] Copied.

REM ---------------- 5. result ----------------
echo.
echo [5/5] Opening the entry page ^(QR code included^) in your browser ...
echo.
echo ================================================================
echo   PUBLIC ADDRESS
echo.
echo       %PUBURL%
echo.
echo   Open this on iPad / phone / WeChat browser.
echo   Free-plan domain changes about every 24h - just re-run this
echo   bat to refresh the QR code and this page.
echo ================================================================
echo.
echo   Service must stay running: do NOT close the "AL Study Service"
echo   window. This PC must stay powered on.
echo.
pause
