@echo off
setlocal EnableExtensions

REM One-click launcher for Gemstone backend + UngdrooFish backend.
REM You can override paths/commands with environment variables:
REM   GEMSTONE_BACKEND_DIR
REM   UNGDROOFISH_BACKEND_DIR
REM   GEMSTONE_START_CMD
REM   UNGDROOFISH_START_CMD

set "ROOT=%~dp0"
set "GEMSTONE_BACKEND_DIR=%ROOT%..\backend"
set "UNGDROOFISH_BACKEND_DIR=%ROOT%backend"

if defined GEMSTONE_BACKEND_DIR set "GEMSTONE_BACKEND_DIR=%GEMSTONE_BACKEND_DIR%"
if defined UNGDROOFISH_BACKEND_DIR set "UNGDROOFISH_BACKEND_DIR=%UNGDROOFISH_BACKEND_DIR%"

set "GEMSTONE_START_CMD=python -m uv run python run.py"
set "UNGDROOFISH_START_CMD=python -m uv run python run.py"

if defined GEMSTONE_START_CMD set "GEMSTONE_START_CMD=%GEMSTONE_START_CMD%"
if defined UNGDROOFISH_START_CMD set "UNGDROOFISH_START_CMD=%UNGDROOFISH_START_CMD%"

echo [INFO] Gemstone backend dir: %GEMSTONE_BACKEND_DIR%
echo [INFO] UngdrooFish backend dir: %UNGDROOFISH_BACKEND_DIR%

if not exist "%UNGDROOFISH_BACKEND_DIR%" (
  echo [ERROR] UngdrooFish backend directory not found.
  echo         %UNGDROOFISH_BACKEND_DIR%
  exit /b 1
)

if not exist "%GEMSTONE_BACKEND_DIR%" (
  echo [WARN] Gemstone backend directory not found.
  echo        %GEMSTONE_BACKEND_DIR%
  echo [WARN] Launching UngdrooFish backend only...
) else (
  start "Gemstone Backend" cmd /k "cd /d ""%GEMSTONE_BACKEND_DIR%"" && %GEMSTONE_START_CMD%"
)

start "UngdrooFish Backend" cmd /k "cd /d ""%UNGDROOFISH_BACKEND_DIR%"" && %UNGDROOFISH_START_CMD%"

echo [DONE] Backend launch commands were sent.
echo        Close each backend window manually to stop services.
exit /b 0

