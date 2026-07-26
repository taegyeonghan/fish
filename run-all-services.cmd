@echo off
setlocal EnableExtensions

REM One-click smart launcher:
REM - Gemstone frontend/backend
REM - UngdrooFish frontend/backend
REM If Gemstone backend path is different, ask once and persist in .launcher.env

set "ROOT=%~dp0"
set "CFG_FILE=%ROOT%.launcher.env"
set "GEMSTONE_FRONTEND_DIR=%ROOT%..\frontend"
set "GEMSTONE_BACKEND_DIR=%ROOT%..\backend"
set "UNGDROOFISH_FRONTEND_DIR=%ROOT%frontend"
set "UNGDROOFISH_BACKEND_DIR=%ROOT%backend"

if exist "%CFG_FILE%" (
  for /f "usebackq tokens=1,* delims==" %%A in ("%CFG_FILE%") do (
    if /i "%%A"=="GEMSTONE_BACKEND_DIR" set "GEMSTONE_BACKEND_DIR=%%B"
    if /i "%%A"=="GEMSTONE_FRONTEND_DIR" set "GEMSTONE_FRONTEND_DIR=%%B"
  )
)

if not exist "%GEMSTONE_BACKEND_DIR%" (
  echo [SETUP] Gemstone backend path not found.
  set /p GEMSTONE_BACKEND_DIR=Enter full path of Gemstone backend directory: 
)

if not exist "%GEMSTONE_FRONTEND_DIR%" (
  echo [SETUP] Gemstone frontend path not found.
  set /p GEMSTONE_FRONTEND_DIR=Enter full path of Gemstone frontend directory (or leave empty): 
)

(
  echo GEMSTONE_BACKEND_DIR=%GEMSTONE_BACKEND_DIR%
  echo GEMSTONE_FRONTEND_DIR=%GEMSTONE_FRONTEND_DIR%
)> "%CFG_FILE%"

echo [INFO] Gemstone frontend : %GEMSTONE_FRONTEND_DIR%
echo [INFO] Gemstone backend  : %GEMSTONE_BACKEND_DIR%
echo [INFO] Fish frontend     : %UNGDROOFISH_FRONTEND_DIR%
echo [INFO] Fish backend      : %UNGDROOFISH_BACKEND_DIR%

if not "%GEMSTONE_FRONTEND_DIR%"=="" if exist "%GEMSTONE_FRONTEND_DIR%" (
  start "Gemstone Frontend" cmd /k "cd /d ""%GEMSTONE_FRONTEND_DIR%"" && npm run dev"
) else (
  echo [WARN] Gemstone frontend directory not found.
)

if not "%GEMSTONE_BACKEND_DIR%"=="" if exist "%GEMSTONE_BACKEND_DIR%" (
  start "Gemstone Backend" cmd /k "cd /d ""%GEMSTONE_BACKEND_DIR%"" && python -m uv run python run.py"
) else (
  echo [WARN] Gemstone backend directory not found.
)

if exist "%UNGDROOFISH_FRONTEND_DIR%" (
  start "UngdrooFish Frontend" cmd /k "cd /d ""%UNGDROOFISH_FRONTEND_DIR%"" && npm run dev"
) else (
  echo [WARN] UngdrooFish frontend directory not found.
)

if exist "%UNGDROOFISH_BACKEND_DIR%" (
  start "UngdrooFish Backend" cmd /k "cd /d ""%UNGDROOFISH_BACKEND_DIR%"" && python -m uv run python run.py"
) else (
  echo [WARN] UngdrooFish backend directory not found.
)

echo [DONE] Launch commands sent.
echo        Close each window manually to stop.
exit /b 0
