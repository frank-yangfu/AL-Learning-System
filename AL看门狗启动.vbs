' AL Study System - watchdog launcher (ASCII only on purpose)
' Launches al_watchdog.py with pythonw.exe, no console window.
Option Explicit

Dim fso, here, py, ws, wmi, col

Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)
py = "C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\pythonw.exe"

If Not fso.FileExists(py) Then
  MsgBox "pythonw.exe not found:" & vbCrLf & py, 16, "AL Study System"
  WScript.Quit 1
End If

If Not fso.FileExists(here & "\al_watchdog.py") Then
  MsgBox "al_watchdog.py not found in:" & vbCrLf & here, 16, "AL Study System"
  WScript.Quit 1
End If

' avoid duplicate watchdogs
On Error Resume Next
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set col = wmi.ExecQuery("SELECT ProcessId FROM Win32_Process WHERE Name='pythonw.exe' AND CommandLine LIKE '%al_watchdog.py%'")
If Err.Number = 0 Then
  If col.Count > 0 Then WScript.Quit 0
End If
On Error GoTo 0

Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = here
ws.Run """" & py & """ """ & here & "\al_watchdog.py""", 0, False
