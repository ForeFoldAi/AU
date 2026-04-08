"""Employee dataclass — shared by Weekly Off tab (API → Employee rows)."""

from __future__ import annotations

from dataclasses import dataclass

from forefold_attendance_gui.api.client import PersonnelData


def _parse_shift_from_raw(raw: dict) -> str:
    """Best-effort shift label from BioTime-style employee payload."""
    s = raw.get("shift")
    if isinstance(s, str) and s.strip():
        return s.strip()
    if isinstance(s, dict):
        for k in ("shift_name", "name", "alias"):
            v = s.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    for k in ("shift_name", "default_shift", "work_shift"):
        v = raw.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "—"


@dataclass
class Employee:
    emp_id:     str
    name:       str
    position:   str
    department: str
    area:       str
    shift:      str
    status:     str = "Active"

    @classmethod
    def from_api(cls, raw: dict) -> "Employee":
        emp_id = str(raw.get("emp_code") or raw.get("id") or "")

        first = (raw.get("first_name") or "").strip()
        last  = (raw.get("last_name")  or "").strip()
        name  = f"{first} {last}".strip() or f"EMP-{emp_id}"

        dept_obj   = raw.get("department") or {}
        department = dept_obj.get("dept_name") or dept_obj.get("name") or "—"

        pos_obj  = raw.get("position") or {}
        position = (
            pos_obj.get("position_name")
            or pos_obj.get("name")
            or "—"
        )
        if position.strip("-") == "":
            position = "—"

        area_list = raw.get("area") or []
        if area_list and isinstance(area_list, list):
            a0 = area_list[0]
            area = a0.get("area_name") or a0.get("name") or "General"
        else:
            area = raw.get("area_name") or "General"

        shift = _parse_shift_from_raw(raw)

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
            area=area,
            shift=shift,
            status=status,
        )


def employees_from_api(data: PersonnelData) -> list[Employee]:
    """Convert a full PersonnelData response to Employee objects."""
    return [Employee.from_api(raw) for raw in data.employees]
