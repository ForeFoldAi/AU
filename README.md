# ForeFold Attendance Report (PySide6 + Nuitka + Inno Setup)

Production-style Windows project for generating monthly BioTime attendance and OT Excel reports.

## Stack

- GUI: `PySide6`
- Core report logic: `requests`, `openpyxl`
- Packaging: `Nuitka` (`--onefile`)
- Installer: `Inno Setup`

## Project Layout

- `src/forefold_attendance/engine.py` - core wrapper for report generation and auth test
- `src/forefold_attendance/cli.py` - CLI entrypoint
- `src/forefold_attendance_gui/main.py` - PySide6 desktop app
- `attendance_report.py` - legacy logic module (still used internally by engine wrapper)
- `run_gui.py` - GUI launcher target used by Nuitka
- `run_cli.py` - CLI launcher
- `build_nuitka.bat` - one-click Windows build for single EXE
- `installer.iss` - Inno Setup installer script

## Development Run

Create virtual env and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run GUI:

```bash
python run_gui.py
```

Run CLI:

```bash
python run_cli.py --base-url "https://your-server" --company "your-company" --email "you@domain.com" --password "secret" --month 4 --year 2026 --output "Attendance_April_2026.xlsx"
```

## Production Build

### Windows — `.exe` (recommended for a true EXE)

From the project folder (PowerShell or CMD):

```bat
build_nuitka.bat
```

Output:

`build\AttendanceReport.exe`

Requires: Python 3.10+ on PATH, a C compiler (Nuitka will hint if missing; MSVC Build Tools on Windows).

### macOS / Linux — single binary (not `.exe`)

`.exe` is a Windows format. On macOS/Linux use:

```bash
./build_nuitka.sh
```

Output:

`build/AttendanceReport`

To ship a **Windows `.exe`**, build on Windows (or a Windows VM/CI) using `build_nuitka.bat`.

## Installer Build (Windows)

1. Install Inno Setup.
2. Open `installer.iss`.
3. Compile.
4. Output installer:

`build\installer\AttendanceReportSetup.exe`

## Security Guidelines

- Do not hardcode real credentials in source files.
- Enter credentials at runtime in the GUI.
- If needed, pass credentials through secured runtime channels in enterprise environments.
