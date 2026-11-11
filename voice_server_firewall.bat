@echo off
chcp 65001 >nul
title AL Learning System - Allow LAN access (TCP 8000)

REM ===================================================================
REM  Adds a Windows Firewall inbound rule for TCP 8000 so that a phone
REM  on the same WiFi can reach the voice server (edge-tts).
REM  Needed when the phone shows "connection failed / timeout" in
REM  Settings - Test voice server.
REM  Adding a firewall rule requires Administrator rights, so this
REM  script re-launches itself elevated.
REM ===================================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

set PORT=8000
echo.
echo ============================================================
echo   Allow inbound TCP %PORT%  (voice server for phones)
echo ============================================================
echo.

netsh advfirewall firewall delete rule name="AL Learning System TTS %PORT%" >nul 2>&1
netsh advfirewall firewall add rule name="AL Learning System TTS %PORT%" dir=in action=allow protocol=TCP localport=%PORT% profile=any >nul
if %errorlevel% equ 0 (
    echo [OK] Firewall rule added: inbound TCP %PORT% allowed ^(all profiles^).
) else (
    echo [!] Failed to add the rule. Right-click this file and choose "Run as administrator".
)
echo.
echo Next steps:
echo   1. Double-click the AL voice launcher to start the server.
echo   2. In the app: Settings - TTS server address - type the LAN IP shown
echo      in the server window, tap Save, then tap Test voice server.
echo.
pause
