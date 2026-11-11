@echo off
chcp 65001 >nul
title AL Self-Study System (voice edition / venv python + edge-tts)

REM ===================================================================
REM  IMPORTANT: must use the isolated venv Python that has edge-tts,
REM  otherwise /api/tts returns 500 and reading-aloud goes silent.
REM
REM  Console output of THIS script is pure ASCII on purpose.
REM  Chinese text only belongs in the web pages, not in the console.
REM  (chcp 65001 is kept so the server's own UTF-8 log renders fine.)
REM
REM  cd /d "%~dp0" avoids hard-coding the project path, so a Chinese
REM  path never gets echoed to the console.
REM ===================================================================
set VENV=C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe

"%VENV%" -c "import edge_tts" >nul 2>&1 && (
    echo [OK] edge-tts is ready ^(venv python^)
) || (
    echo [!] edge-tts missing, installing...
    "%VENV%" -m pip install edge-tts
)

cd /d "%~dp0"

echo.
echo ============================================================
echo  AL Self-Study System  ^(port 8000, voice reading enabled^)
echo  Open in browser:  http://localhost:8000
echo.
echo  PHONE with no built-in speech engine ^(e.g. Huawei^):
echo  copy the "phone / tablet address" line printed below into
echo  the app:  Settings - TTS server address, tap Save, then
echo  tap "Test voice server".
echo.
echo  If that test fails, run this once ^(needs admin^):
echo      voice_server_firewall.bat
echo.
echo  Close this window to stop the server.
echo ============================================================
echo.

"%VENV%" server.py
pause
