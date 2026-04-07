"""Background worker for report generation and authentication."""

from __future__ import annotations

import traceback

from PySide6.QtCore import QObject, Signal

from forefold_attendance.engine import generate_report, test_auth


class ReportWorker(QObject):
    log = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, cfg: dict, output: str, auth_only: bool):
        super().__init__()
        self.cfg = cfg
        self.output = output
        self.auth_only = auth_only

    def run(self):
        try:
            if self.auth_only:
                logs = test_auth(self.cfg)
                if logs:
                    self.log.emit(logs)
                self.finished.emit("Authentication successful.")
                return

            output_path, logs = generate_report(self.cfg, self.output or None)
            if logs:
                self.log.emit(logs)
            self.finished.emit(f"Report saved: {output_path}")
        except Exception as exc:
            self.failed.emit(f"{exc}\n\n{traceback.format_exc()}")
