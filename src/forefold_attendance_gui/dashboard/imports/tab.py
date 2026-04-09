"""Imports tab - import three Excel masters for scheduling data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from forefold_attendance_gui import imports_store


class ImportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_manifest_into_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Data Imports")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "Import three Excel masters. "
            "Shift: Shift Name, Timetable, Unit, Cycle, Auto Shift. "
            "Timetable: Name (shift name), Type, Check In, Check Out, Work Time, Break Time, "
            "WorkDay, Work Type, First Half (Check Out Time), Second Half (Check In Time). "
            "Schedule: Employee Id, First Name, Shift Name, Start Date, End Date. "
            "Weekly Off uses schedule → shift → timetable to show Shift and Shift timing."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("sectionSubtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #E2E8F0;")
        root.addWidget(divider)

        card = QGroupBox("Import Files")
        form = QFormLayout(card)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.shift_path = self._path_row("Shift Times", self._pick_shift)
        self.timetable_path = self._path_row("Timetable", self._pick_timetable)
        self.schedule_path = self._path_row(
            "Employee Scheduled Shifts", self._pick_schedule
        )

        form.addRow("Shift Times", self.shift_path["row"])
        form.addRow("Timetable", self.timetable_path["row"])
        form.addRow("Employee Scheduled Shifts", self.schedule_path["row"])
        root.addWidget(card)

        actions = QHBoxLayout()
        self.import_btn = QPushButton("Import Files")
        self.import_btn.setObjectName("primaryButton")
        self.import_btn.clicked.connect(self._import_files)

        self.clear_btn = QPushButton("Clear Selections")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self._clear_selection)

        actions.addWidget(self.import_btn)
        actions.addWidget(self.clear_btn)
        actions.addStretch(1)
        root.addLayout(actions)

        self.status = QLabel("")
        self.status.setObjectName("sectionSubtitle")
        root.addWidget(self.status)
        root.addStretch(1)

    def _path_row(self, placeholder: str, on_browse: Callable[[], None]) -> dict[str, Any]:
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        txt = QLineEdit()
        txt.setPlaceholderText(f"Select {placeholder} Excel file")

        browse = QPushButton("Browse...")
        browse.clicked.connect(on_browse)
        browse.setFixedWidth(100)

        lay.addWidget(txt, 1)
        lay.addWidget(browse)
        return {"row": row, "input": txt}

    def _start_dir(self) -> str:
        d = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        return d or str(Path.home())

    def _pick_excel(self, target: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel file",
            self._start_dir(),
            "Excel Files (*.xlsx *.xlsm *.xltx *.xltm)",
        )
        if path:
            target.setText(path)

    def _pick_shift(self) -> None:
        self._pick_excel(self.shift_path["input"])

    def _pick_timetable(self) -> None:
        self._pick_excel(self.timetable_path["input"])

    def _pick_schedule(self) -> None:
        self._pick_excel(self.schedule_path["input"])

    def _clear_selection(self) -> None:
        self.shift_path["input"].clear()
        self.timetable_path["input"].clear()
        self.schedule_path["input"].clear()

    def _load_manifest_into_ui(self) -> None:
        manifest = imports_store.load_manifest()
        mapping = [
            (imports_store.KIND_SHIFT_TIMES, self.shift_path["input"]),
            (imports_store.KIND_TIMETABLE, self.timetable_path["input"]),
            (imports_store.KIND_EMPLOYEE_SCHEDULE, self.schedule_path["input"]),
        ]
        loaded = 0
        for kind, target in mapping:
            rec = manifest.get(kind) or {}
            p = rec.get("source_path") or rec.get("stored_path") or ""
            if p:
                target.setText(str(p))
                loaded += 1
        if loaded:
            self.status.setText(f"Loaded {loaded}/3 previously imported file paths.")

    def _import_files(self) -> None:
        files = {
            imports_store.KIND_SHIFT_TIMES: self.shift_path["input"].text().strip(),
            imports_store.KIND_TIMETABLE: self.timetable_path["input"].text().strip(),
            imports_store.KIND_EMPLOYEE_SCHEDULE: self.schedule_path["input"].text().strip(),
        }

        missing = [k for k, p in files.items() if not p]
        if missing:
            QMessageBox.warning(
                self,
                "Missing files",
                "Please select all three files before importing.\n\nMissing: "
                + ", ".join(imports_store.kind_label(k) for k in missing),
            )
            return

        try:
            results = imports_store.import_all(files)
        except Exception as exc:
            QMessageBox.critical(self, "Import Failed", str(exc))
            return

        msg = "\n".join(
            f"- {imports_store.kind_label(kind)}: {info['row_count']} rows ({info['sheet_name']})"
            for kind, info in results.items()
        )
        self.status.setText("Imported successfully.")
        QMessageBox.information(
            self,
            "Import Complete",
            f"Files imported successfully.\n\n{msg}",
        )
