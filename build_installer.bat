@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ==============================================
echo   Build EXE, then Inno Setup installer
echo ==============================================
echo.

call build_nuitka.bat
if errorlevel 1 (
  echo ERROR: Nuitka build failed.
  exit /b 1
)

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC where iscc >nul 2>&1 && set "ISCC=iscc"

if not defined ISCC (
  echo ERROR: Inno Setup Compiler ^(ISCC.exe^) not found.
  echo Install Inno Setup 6 from https://jrsoftware.org/isdl.php
  echo Then run this script again, or add ISCC.exe to PATH.
  exit /b 1
)

echo Compiling installer with: %ISCC%
"%ISCC%" "%~dp0installer.iss"
if errorlevel 1 (
  echo ERROR: Inno Setup compile failed.
  exit /b 1
)

echo.
echo Done. Installer: build\installer\AttendanceReportSetup.exe
echo.
endlocal
