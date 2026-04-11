@echo off
setlocal EnableExtensions

REM Production build for Windows:
REM - GUI: PySide6
REM - Compiler: Nuitka (standalone folder - Windows friendly)
REM - Output: build\AttendanceReport.dist\AttendanceReport.exe

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
python -m pip install "nuitka[onefile]>=2.4"
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
  --standalone ^
  --assume-yes-for-downloads ^
  --windows-console-mode=disable ^
  --enable-plugin=pyside6 ^
  --include-qt-plugins=platforms,styles,imageformats ^
  --include-module=attendance_report ^
  --include-data-files=src/public/forefold-logo.png=forefold-logo.png ^
  --windows-company-name="ForeFold AI" ^
  --windows-product-name="ForeFold Report Generator" ^
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
if exist build\run_gui.dist (
  if exist build\AttendanceReport.dist rmdir /s /q build\AttendanceReport.dist
  move /Y build\run_gui.dist build\AttendanceReport.dist >NUL
)
if not exist build\AttendanceReport.dist (
  for /d %%D in (build\*.dist) do (
    if /I not "%%~nxD"=="AttendanceReport.dist" (
      if exist build\AttendanceReport.dist rmdir /s /q build\AttendanceReport.dist
      move /Y "%%D" build\AttendanceReport.dist >NUL
      goto :dist_done
    )
  )
)
:dist_done
if not exist build\AttendanceReport.dist\AttendanceReport.exe (
  echo ERROR: Expected build\AttendanceReport.dist\AttendanceReport.exe not found.
  exit /b 1
)
echo EXE: build\AttendanceReport.dist\AttendanceReport.exe
echo.
endlocal
