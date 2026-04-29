@echo off
setlocal

rem Persist environment variables required by PowerShell/node-pty/Codex on Windows.
setx SystemRoot "C:\Windows"
setx WINDIR "C:\Windows"
setx ComSpec "C:\Windows\System32\cmd.exe"
setx PSModulePath "%USERPROFILE%\Documents\WindowsPowerShell\Modules;C:\Program Files\WindowsPowerShell\Modules;C:\Windows\System32\WindowsPowerShell\v1.0\Modules"

echo.
echo Persistent environment variables were written for the current user.
echo Fully close VS Code/Codex, then start them again.
echo.
pause
