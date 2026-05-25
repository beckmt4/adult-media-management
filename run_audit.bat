@echo off
powershell.exe -ExecutionPolicy Bypass -NonInteractive -File "%~dp0audit_unraid.ps1"
echo Exit code: %ERRORLEVEL%
pause
