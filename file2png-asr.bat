@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%work"
set "LOG_FILE=%LOG_DIR%\file2png-launcher.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul
>>"%LOG_FILE%" echo [%DATE% %TIME%] START file2png-asr args=%*

if "%~1"=="" (
  >>"%LOG_FILE%" echo [%DATE% %TIME%] ERROR no selected files were passed
  exit /b 2
)

if exist "%SystemRoot%\py.exe" (
  "%SystemRoot%\py.exe" -3 "%SCRIPT_DIR%file2png.py" --src %*
  set "EXIT_CODE=%ERRORLEVEL%"
  >>"%LOG_FILE%" echo [%DATE% %TIME%] EXIT py.exe code=!EXIT_CODE!
  exit /b !EXIT_CODE!
)

where py.exe >nul 2>nul
if not errorlevel 1 (
  py.exe -3 "%SCRIPT_DIR%file2png.py" --src %*
  set "EXIT_CODE=%ERRORLEVEL%"
  >>"%LOG_FILE%" echo [%DATE% %TIME%] EXIT py.exe-path code=!EXIT_CODE!
  exit /b !EXIT_CODE!
)

where python.exe >nul 2>nul
if not errorlevel 1 (
  python.exe "%SCRIPT_DIR%file2png.py" --src %*
  set "EXIT_CODE=%ERRORLEVEL%"
  >>"%LOG_FILE%" echo [%DATE% %TIME%] EXIT python.exe-path code=!EXIT_CODE!
  exit /b !EXIT_CODE!
)

>>"%LOG_FILE%" echo [%DATE% %TIME%] ERROR Python was not found
exit /b 9009
