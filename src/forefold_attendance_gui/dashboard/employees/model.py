"""Employee data model — dataclass + QAbstractTableModel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from forefold_attendance_gui.api.client import PersonnelData


# ─────────────────────────────────────────────────────────────────────────────
#  Employee dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Employee:
    emp_id:     str
    name:       str
    position:   str
    department: str
    shift:      str
    status:     str = "Active"

    @classmethod
    def from_api(cls, raw: dict) -> "Employee":
        """
        Map a raw BioTime API employee dict to an Employee instance.

        Actual response shape (confirmed):
          - department : {"id": 9376, "dept_code": "GAR", "dept_name": "Gardners"}
          - position   : {"id": 8592, "position_code": "GAR", "position_name": "Gardner"}
          - area       : [{"id": 7473, "area_code": "2", "area_name": "Cyber Towers"}]
          - enable_att : true/false  → Active / Inactive
        """
        emp_id = str(raw.get("emp_code") or raw.get("id") or "")

        # Name
        first = (raw.get("first_name") or "").strip()
        last  = (raw.get("last_name")  or "").strip()
        name  = f"{first} {last}".strip() or f"EMP-{emp_id}"

        # Department — nested dict
        dept_obj   = raw.get("department") or {}
        department = dept_obj.get("dept_name") or dept_obj.get("name") or "—"

        # Position — nested dict
        pos_obj  = raw.get("position") or {}
        position = (
            pos_obj.get("position_name")
            or pos_obj.get("name")
            or "—"
        )
        # Skip placeholder positions like "-"
        if position.strip("-") == "":
            position = "—"

        # Area — list of dicts; show first entry or "General"
        area_list = raw.get("area") or []
        if area_list and isinstance(area_list, list):
            shift = area_list[0].get("area_name") or area_list[0].get("name") or "General"
        else:
            shift = raw.get("area_name") or "General"

        # Status — enable_att bool
        enable_att = raw.get("enable_att")
        if isinstance(enable_att, bool):
            status = "Active" if enable_att else "Inactive"
        else:
            status = "Active"

        return cls(
            emp_id=emp_id,
            name=name,
            position=position,
            department=department,
            shift=shift,
            status=status,
        )


def employees_from_api(data: PersonnelData) -> list[Employee]:
    """
    Convert a full PersonnelData response to Employee objects.
    Department, position, and area are already nested in each employee record,
    so no separate lookup maps are required.
    """
    return [Employee.from_api(raw) for raw in data.employees]


# ─────────────────────────────────────────────────────────────────────────────
#  Qt Table Model
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = ["Emp ID", "Name", "Position", "Department", "Shift", "Status"]

COL_EMP_ID     = 0
COL_NAME       = 1
COL_POSITION   = 2
COL_DEPARTMENT = 3
COL_SHIFT      = 4
COL_STATUS     = 5


class EmployeeTableModel(QAbstractTableModel):
    def __init__(self, employees: list[Employee] | None = None, parent=None):
        super().__init__(parent)
        self._data: list[Employee] = employees or []

    # ── Required overrides ────────────────────────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        emp = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return _cell_text(emp, col)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignVCenter | Qt.AlignLeft

        if role == Qt.ItemDataRole.ForegroundRole:
            from PySide6.QtGui import QColor
            return QColor("#1E293B")

        if role == Qt.ItemDataRole.UserRole:
            return emp

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Horizontal:
            return HEADERS[section]
        return None

    # ── Public API ────────────────────────────────────────────────────────────

    def reload(self, employees: list[Employee]) -> None:
        self.beginResetModel()
        self._data = employees
        self.endResetModel()

    def employee_at(self, row: int) -> Employee | None:
        return self._data[row] if 0 <= row < len(self._data) else None


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cell_text(emp: Employee, col: int) -> str:
    return (
        emp.emp_id,
        emp.name,
        emp.position,
        emp.department,
        emp.shift,
        emp.status,
    )[col]
