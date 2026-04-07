"""Reports tab – attendance report generation UI."""

from __future__ import annotations

import calendar
from datetime import datetime

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QColor, QFont, QTextCursor
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
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QTextEdit,
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
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Section header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Attendance Reports")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Generate and export monthly attendance reports.")
        subtitle.setObjectName("sectionSubtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #E2E8F0;")
        root.addWidget(divider)

        # ── Report Configuration ─────────────────────────────────────────────
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

        # ── Output ───────────────────────────────────────────────────────────
        out = QGroupBox("Output")
        out_row = QHBoxLayout(out)
        out_row.setSpacing(10)
        self.output = QLineEdit()
        self.output.setPlaceholderText("Optional: choose where to save the report")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_output)
        out_row.addWidget(QLabel("Save As"))
        out_row.addWidget(self.output, 1)
        out_row.addWidget(browse)
        root.addWidget(out)

        # ── Actions ──────────────────────────────────────────────────────────
        actions_box = QGroupBox("Actions")
        buttons = QHBoxLayout(actions_box)
        buttons.setSpacing(10)
        self.btn_run = QPushButton("Generate Report")
        self.btn_run.setObjectName("primaryButton")
        self.btn_auth = QPushButton("Test Authentication")
        self.btn_auth.setObjectName("secondaryButton")
        self.btn_clear = QPushButton("Clear Log")
        self.btn_clear.setObjectName("tertiaryButton")
        self.btn_run.clicked.connect(self._run_report)
        self.btn_auth.clicked.connect(self._run_auth)
        self.btn_clear.clicked.connect(self._clear_log)
        buttons.addWidget(self.btn_run)
        buttons.addWidget(self.btn_auth)
        buttons.addWidget(self.btn_clear)
        buttons.addStretch(1)
        root.addWidget(actions_box)

        # ── Log ──────────────────────────────────────────────────────────────
        logs_box = QGroupBox("Execution Log")
        logs_layout = QVBoxLayout(logs_box)
        self.log = QTextEdit()
        self.log.setObjectName("logView")
        self.log.setReadOnly(True)
        self.log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log.setPlaceholderText("Execution logs will appear here…")
        self.log.setFont(QFont("Consolas", 9))
        logs_layout.addWidget(self.log)
        root.addWidget(logs_box, 1)

        self._update_actions_enabled()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _browse_output(self):
        default = f"Attendance_{self.month.currentText()}_{self.year.value()}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Select Output Path", default, "Excel Files (*.xlsx)"
        )
        if path:
            self.output.setText(path)

    def _clear_log(self):
        self.log.clear()

    def _run_auth(self):
        self._execute(auth_only=True)

    def _run_report(self):
        self._execute(auth_only=False)

    def _execute(self, auth_only: bool):
        cfg = self._build_cfg()
        self._set_busy(True)
        self._log_info(
            f"Starting {'authentication test' if auth_only else 'report generation'}…"
        )
        self._thread = QThread(self)
        self._worker = ReportWorker(cfg, self.output.text().strip(), auth_only)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._log_info)
        self._worker.finished.connect(self._on_success)
        self._worker.failed.connect(self._on_error)
        self._worker.finished.connect(self._cleanup_thread)
        self._worker.failed.connect(self._cleanup_thread)
        self._thread.start()

    def _on_success(self, message: str):
        self._log_success(message)
        self._set_busy(False)
        self._status_bar.showMessage("Done")
        QMessageBox.information(self, "Success", message)

    def _on_error(self, message: str):
        self._log_error(message)
        self._set_busy(False)
        self._status_bar.showMessage("Error")
        QMessageBox.critical(self, "Error", message.splitlines()[0])

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
        can = not self._thread_is_running
        self.btn_run.setEnabled(can)
        self.btn_auth.setEnabled(can)

    def _append_log(self, text: str, color: str):
        if not text:
            return
        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log.setTextCursor(cursor)
        self.log.setTextColor(QColor(color))
        self.log.insertPlainText(text + "\n")
        self.log.ensureCursorVisible()

    def _log_info(self, text: str):
        self._append_log(text, "#94A3B8")

    def _log_success(self, text: str):
        self._append_log(text, "#4ADE80")

    def _log_error(self, text: str):
        self._append_log(text, "#F87171")
