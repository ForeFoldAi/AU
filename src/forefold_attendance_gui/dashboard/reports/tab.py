"""Reports tab – attendance report generation UI."""

from __future__ import annotations

import calendar
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from forefold_attendance_gui.constants import (
    BACKEND_BASE_URL,
    BACKEND_COMPANY,
    COMPANY_NAME,
    DEFAULT_STANDARD_HOURS,
    PAGE_SIZE,
    SITE_NAME,
)
from forefold_attendance_gui.dashboard.reports.worker import ReportWorker


class ReportsTab(QWidget):
    """Tab widget containing the attendance report generation interface."""

    def __init__(self, email: str, password: str, status_bar: QStatusBar):
        super().__init__()
        self.user_email = email
        self.user_password = password
        self._status_bar = status_bar
        self._thread: QThread | None = None
        self._worker: ReportWorker | None = None
        self._thread_is_running = False
        self._output_manual = False
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Attendance Reports")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Generate and export monthly attendance reports.")
        subtitle.setObjectName("sectionSubtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #E2E8F0;")
        root.addWidget(divider)

        period = QGroupBox("Report Configuration")
        period_grid = QGridLayout(period)
        period_grid.setSpacing(10)

        self.month = QComboBox()
        self.month.addItems([calendar.month_name[m] for m in range(1, 13)])
        self.month.setCurrentIndex(datetime.now().month - 1)

        now_year = datetime.now().year
        self.year = QSpinBox()
        self.year.setRange(now_year - 10, now_year + 10)
        self.year.setValue(now_year)

        period_grid.addWidget(QLabel("Month"), 0, 0)
        period_grid.addWidget(self.month, 0, 1)
        period_grid.addWidget(QLabel("Year"), 0, 2)
        period_grid.addWidget(self.year, 0, 3)
        period_grid.setColumnStretch(4, 1)
        root.addWidget(period)

        out = QGroupBox("Output")
        out_row = QHBoxLayout(out)
        out_row.setSpacing(10)
        self.output = QLineEdit()
        self.output.setPlaceholderText("Save location (default: Downloads)")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_output)
        out_row.addWidget(QLabel("Save As"))
        out_row.addWidget(self.output, 1)
        out_row.addWidget(browse)
        root.addWidget(out)

        actions_box = QGroupBox("Actions")
        buttons = QHBoxLayout(actions_box)
        buttons.setSpacing(10)
        self.btn_run = QPushButton("Generate Report")
        self.btn_run.setObjectName("primaryButton")
        self.btn_run.clicked.connect(self._run_report)
        buttons.addWidget(self.btn_run)
        buttons.addStretch(1)
        root.addWidget(actions_box)

        root.addStretch(1)

        self.month.currentIndexChanged.connect(self._on_period_changed)
        self.year.valueChanged.connect(self._on_period_changed)

        self._apply_default_output_path()
        self._update_actions_enabled()

    def _downloads_dir(self) -> Path | None:
        loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        return Path(loc) if loc else None

    def _default_report_filename(self) -> str:
        mo = calendar.month_name[self.month.currentIndex() + 1]
        return f"Attendance_{mo}_{self.year.value()}.xlsx"

    def _apply_default_output_path(self) -> None:
        if self._output_manual:
            return
        base = self._downloads_dir()
        if base:
            self.output.setText(str(base / self._default_report_filename()))

    def _on_period_changed(self) -> None:
        self._apply_default_output_path()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _browse_output(self):
        default = self._default_report_filename()
        base = self._downloads_dir() or Path.home()
        path, _ = QFileDialog.getSaveFileName(
            self, "Select Output Path", str(base / default), "Excel Files (*.xlsx)"
        )
        if path:
            self._output_manual = True
            self.output.setText(path)

    def _run_report(self):
        self._execute()

    def _execute(self) -> None:
        out = self.output.text().strip()
        if not out:
            self._apply_default_output_path()
            out = self.output.text().strip()
        if not out:
            QMessageBox.warning(self, "Output path", "Choose where to save the report.")
            return

        cfg = self._build_cfg()
        self._set_busy(True)
        self._thread = QThread(self)
        self._worker = ReportWorker(cfg, out, auth_only=False)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_success)
        self._worker.failed.connect(self._on_error)
        self._worker.finished.connect(self._cleanup_thread)
        self._worker.failed.connect(self._cleanup_thread)
        self._thread.start()

    def _on_success(self, message: str):
        self._set_busy(False)
        self._status_bar.showMessage("Done")
        QMessageBox.information(self, "Success", message)

    def _on_error(self, message: str):
        self._set_busy(False)
        self._status_bar.showMessage("Error")
        first = message.strip().splitlines()[0] if message.strip() else "Something went wrong."
        QMessageBox.critical(self, "Error", first)

    def _cleanup_thread(self):
        if self._thread:
            self._thread.quit()
            self._thread.wait()
        self._thread = None
        self._worker = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_cfg(self) -> dict:
        return {
            "base_url": BACKEND_BASE_URL,
            "company": BACKEND_COMPANY,
            "email": self.user_email,
            "password": self.user_password,
            "month": self.month.currentIndex() + 1,
            "year": int(self.year.value()),
            "company_name": COMPANY_NAME,
            "site_name": SITE_NAME,
            "page_size": PAGE_SIZE,
            "default_standard_hours": DEFAULT_STANDARD_HOURS,
            "default_weekly_off_days": [6],
        }

    def _set_busy(self, busy: bool):
        self._thread_is_running = busy
        self._update_actions_enabled()
        self._status_bar.showMessage("Processing…" if busy else "Ready")

    def _update_actions_enabled(self):
        self.btn_run.setEnabled(not self._thread_is_running)
