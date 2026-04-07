"""Reusable dialogs for the Reports section."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class WeeklyOffDialog(QDialog):
    DAY_LABELS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    def __init__(self, selected_days: list[int], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Configure Weekly Offs")
        self.setModal(True)
        self.setMinimumWidth(360)
        self._checks: list[QCheckBox] = []

        root = QVBoxLayout(self)
        root.setSpacing(12)

        info = QLabel("Select default weekly-off days used for new report runs.")
        info.setWordWrap(True)
        root.addWidget(info)

        grid = QGridLayout()
        grid.setSpacing(8)
        for idx, label in enumerate(self.DAY_LABELS):
            cb = QCheckBox(label)
            cb.setChecked(idx in selected_days)
            self._checks.append(cb)
            grid.addWidget(cb, idx // 4, idx % 4)
        root.addLayout(grid)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def selected_days(self) -> list[int]:
        return [idx for idx, cb in enumerate(self._checks) if cb.isChecked()]
