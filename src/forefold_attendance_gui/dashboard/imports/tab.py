"""Excel master import — full panel or single-button dialog flow (Weekly Off)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QStandardPaths, Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from forefold_attendance_gui import imports_store


def _start_dir() -> str:
    d = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    return d or str(Path.home())


def _path_row(
    parent: QWidget, placeholder: str, on_browse: Callable[[], None]
) -> dict[str, Any]:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    txt = QLineEdit()
    txt.setPlaceholderText(f"Select {placeholder} Excel file")

    browse = QPushButton("Browse…")
    browse.clicked.connect(on_browse)
    browse.setFixedWidth(100)

    lay.addWidget(txt, 1)
    lay.addWidget(browse)
    return {"row": row, "input": txt}


def run_import_all(files: dict[str, str]) -> tuple[bool, str, bool]:
    """Run ``import_all``.

    Returns ``(success, message, is_validation_error)``.
    """
    missing = [k for k, p in files.items() if not p]
    if missing:
        detail = ", ".join(imports_store.kind_label(k) for k in missing)
        return False, f"Please select all three files.\n\nMissing: {detail}", True

    try:
        results = imports_store.import_all(files)
    except Exception as exc:
        return False, str(exc), False

    msg = "\n".join(
        f"- {imports_store.kind_label(kind)}: {info['row_count']} rows ({info['sheet_name']})"
        for kind, info in results.items()
    )
    return True, msg, False


class ImportMastersDialog(QDialog):
    """Popup to pick three Excel masters and import."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Excel masters")
        self.setModal(True)
        self.resize(580, 320)

        root = QVBoxLayout(self)
        root.setSpacing(14)

        intro = QLabel(
            "Choose Shift Times, Shift time table, and Employee Scheduled Shifts workbooks, "
            "then click Import."
        )
        intro.setObjectName("sectionSubtitle")
        intro.setWordWrap(True)
        root.addWidget(intro)

        card = QGroupBox("Excel files")
        form = QFormLayout(card)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.shift_path = _path_row(self, "Shift Times", self._pick_shift)
        self.timetable_path = _path_row(self, "Shift time table", self._pick_timetable)
        self.schedule_path = _path_row(
            self, "Employee Scheduled Shifts", self._pick_schedule
        )

        form.addRow("Shift Times", self.shift_path["row"])
        form.addRow("Shift time table", self.timetable_path["row"])
        form.addRow("Employee Scheduled Shifts", self.schedule_path["row"])
        root.addWidget(card)

        actions = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self._clear_selection)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        import_btn = QPushButton("Import")
        import_btn.setObjectName("primaryButton")
        import_btn.setDefault(True)
        import_btn.clicked.connect(self._on_import)

        actions.addWidget(clear_btn)
        actions.addStretch(1)
        actions.addWidget(cancel_btn)
        actions.addWidget(import_btn)
        root.addLayout(actions)

        self._load_manifest_into_fields()

    def _pick_excel(self, target: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel file",
            _start_dir(),
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

    def _load_manifest_into_fields(self) -> None:
        manifest = imports_store.load_manifest()
        mapping = [
            (imports_store.KIND_SHIFT_TIMES, self.shift_path["input"]),
            (imports_store.KIND_TIMETABLE, self.timetable_path["input"]),
            (imports_store.KIND_EMPLOYEE_SCHEDULE, self.schedule_path["input"]),
        ]
        for kind, target in mapping:
            rec = manifest.get(kind) or {}
            p = rec.get("source_path") or rec.get("stored_path") or ""
            if p:
                target.setText(str(p))

    def _on_import(self) -> None:
        files = {
            imports_store.KIND_SHIFT_TIMES: self.shift_path["input"].text().strip(),
            imports_store.KIND_TIMETABLE: self.timetable_path["input"].text().strip(),
            imports_store.KIND_EMPLOYEE_SCHEDULE: self.schedule_path["input"].text().strip(),
        }
        ok, msg, validation = run_import_all(files)
        if not ok:
            if validation:
                QMessageBox.warning(self, "Missing files", msg)
            else:
                QMessageBox.critical(self, "Import Failed", msg)
            return

        QMessageBox.information(
            self,
            "Import Complete",
            f"Files imported successfully.\n\n{msg}",
        )
        self.accept()


class ImportsPanel(QWidget):
    """Embedded: single Import button opens :class:`ImportMastersDialog`. Full: inline form."""

    def __init__(self, parent=None, *, embedded: bool = False):
        super().__init__(parent)
        self._embedded = embedded
        self._build_ui()
        if not self._embedded:
            self._load_manifest_into_ui()

    def _build_ui(self) -> None:
        if self._embedded:
            self._build_ui_embedded()
        else:
            self._build_ui_full()

    def _build_ui_embedded(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        self.import_btn = QPushButton("Import…")
        self.import_btn.setObjectName("primaryButton")
        self.import_btn.setFixedSize(100, 36)
        self.import_btn.setToolTip(
            "Import Shift Times, Shift time table, and Employee Scheduled Shifts Excel files"
        )
        self.import_btn.clicked.connect(self._open_import_dialog)
        root.addWidget(self.import_btn)

    def _build_ui_full(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Data Imports")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "Import three Excel masters. "
            "Shift master: Shift Name, Timetable column, Unit, Cycle, Auto Shift. "
            "Shift time table: Name (shift name), Type, Check In, Check Out, Work Time, Break Time, "
            "WorkDay, Work Type, First Half (Check Out Time), Second Half (Check In Time). "
            "Schedule: Employee Id, First Name, Shift Name, Start Date, End Date. "
            "Employee management uses schedule → shift → shift time table to show shift details."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("sectionSubtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #E2E8F0;")
        root.addWidget(divider)

        card = QGroupBox("Import Files")
        form = QFormLayout(card)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.shift_path = _path_row(self, "Shift Times", self._pick_shift)
        self.timetable_path = _path_row(self, "Shift time table", self._pick_timetable)
        self.schedule_path = _path_row(
            self, "Employee Scheduled Shifts", self._pick_schedule
        )

        form.addRow("Shift Times", self.shift_path["row"])
        form.addRow("Shift time table", self.timetable_path["row"])
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

    def _open_import_dialog(self) -> None:
        dlg = ImportMastersDialog(self.window())
        dlg.exec()

    def _pick_excel(self, target: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel file",
            _start_dir(),
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
        ok, msg, validation = run_import_all(files)
        if not ok:
            if validation:
                QMessageBox.warning(self, "Missing files", msg)
            else:
                QMessageBox.critical(self, "Import Failed", msg)
            return

        self.status.setText("Imported successfully.")
        QMessageBox.information(
            self,
            "Import Complete",
            f"Files imported successfully.\n\n{msg}",
        )


__all__ = ["ImportsPanel", "ImportMastersDialog", "run_import_all"]
