#!/usr/bin/env bash
# macOS / Linux: single-file GUI binary (not .exe — use build_nuitka.bat on Windows for .exe).
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "=============================================="
echo "  ForeFold Attendance - Nuitka Build"
echo "=============================================="
echo ""

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is not available in PATH."
  exit 1
fi

echo "[1/4] Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install "nuitka>=2.4"

echo "[2/4] Cleaning old build artifacts..."
rm -rf build run_gui.build run_gui.dist run_gui.onefile-build

echo "[3/4] Compiling with Nuitka..."
# attendance_report.py at repo root is imported by engine — include explicitly.
python3 -m nuitka \
  --onefile \
  --enable-plugin=pyside6 \
  --include-qt-plugins=platforms \
  --include-module=attendance_report \
  --output-dir=build \
  --output-filename=AttendanceReport \
  run_gui.py

echo "[4/4] Build complete."
echo "Binary: build/AttendanceReport"
echo ""
