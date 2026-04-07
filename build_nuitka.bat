@echo off
setlocal EnableExtensions

REM Production build for Windows:
REM - GUI: PySide6
REM - Compiler: Nuitka (single EXE)
REM - Output: build\AttendanceReport.exe

echo.
echo ==============================================
echo   ForeFold Attendance - Nuitka Build
echo ==============================================
echo.

python --version >NUL 2>&1
if errorlevel 1 (
  echo ERROR: Python is not available in PATH.
  exit /b 1
)

echo [1/4] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "nuitka>=2.4"
if errorlevel 1 (
  echo ERROR: Failed installing dependencies.
  exit /b 1
)

echo [2/4] Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist run_gui.build rmdir /s /q run_gui.build
if exist run_gui.dist rmdir /s /q run_gui.dist
if exist run_gui.onefile-build rmdir /s /q run_gui.onefile-build

echo [3/4] Compiling with Nuitka...
REM attendance_report.py lives at repo root and is imported by engine — include explicitly.
python -m nuitka ^
  --onefile ^
  --windows-console-mode=disable ^
  --enable-plugin=pyside6 ^
  --include-qt-plugins=platforms ^
  --include-module=attendance_report ^
  --windows-company-name="AUINFOCITY" ^
  --windows-product-name="Attendance Report" ^
  --windows-file-version=1.0.0.0 ^
  --windows-product-version=1.0.0.0 ^
  --output-dir=build ^
  --output-filename=AttendanceReport.exe ^
  run_gui.py

if errorlevel 1 (
  echo ERROR: Nuitka build failed.
  exit /b 1
)

echo [4/4] Build complete.
echo EXE: build\AttendanceReport.exe
echo.
endlocal
