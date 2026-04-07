"""Production wrapper around the existing attendance engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import calendar
import contextlib
import io
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import attendance_report as legacy  # noqa: E402


@dataclass
class ReportConfig:
    base_url: str
    company: str
    email: str
    password: str
    month: int
    year: int
    company_name: str = "AUINFOCITY"
    site_name: str = "CYBER TOWERS"
    page_size: int = 100
    default_standard_hours: int = 8
    default_weekly_off_days: list[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url.rstrip("/"),
            "company": self.company.strip(),
            "email": self.email.strip(),
            "password": self.password,
            "month": self.month,
            "year": self.year,
            "company_name": self.company_name,
            "site_name": self.site_name,
            "page_size": self.page_size,
            "default_standard_hours": self.default_standard_hours,
            "default_weekly_off_days": self.default_weekly_off_days or [6],
        }


def _validate_config(cfg: Dict[str, Any]) -> None:
    required = ["base_url", "email", "password", "month", "year"]
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        raise ValueError(f"Missing required config values: {', '.join(missing)}")
    if not 1 <= int(cfg["month"]) <= 12:
        raise ValueError("Month must be between 1 and 12")


def _run_with_capture(fn, *args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            result = fn(*args, **kwargs)
        except SystemExit as exc:
            raise RuntimeError("Legacy engine exited unexpectedly") from exc
    return result, buf.getvalue()


def test_auth(cfg: Dict[str, Any]) -> str:
    """Run auth flow and return captured logs."""
    _validate_config(cfg)
    merged_cfg = {**legacy.CONFIG, **cfg}

    def _do_auth():
        client = legacy.BioTimeClient(merged_cfg)
        client.authenticate()
        return True

    _, logs = _run_with_capture(_do_auth)
    return logs


def generate_report(cfg: Dict[str, Any], output: Optional[str] = None) -> tuple[str, str]:
    """
    Generate the attendance report using the legacy logic.

    Returns:
        (output_path, logs)
    """
    _validate_config(cfg)
    merged_cfg = {**legacy.CONFIG, **cfg}
    merged_cfg["password"] = cfg["password"]
    merged_cfg["email"] = cfg["email"]
    merged_cfg["company"] = cfg.get("company", "")
    merged_cfg["base_url"] = cfg["base_url"].rstrip("/")

    mo_name = calendar.month_name[int(merged_cfg["month"])]
    output_path = output or f"Attendance_{mo_name}_{merged_cfg['year']}.xlsx"
    output_path = os.path.abspath(output_path)

    def _do_report():
        legacy.CONFIG.update(merged_cfg)
        client = legacy.BioTimeClient(merged_cfg)
        client.authenticate()
        raw_emps = client.employees()
        raw_depts = client.departments()
        raw_pos = client.positions()

        depts_map = {str(d["id"]): d for d in raw_depts}
        pos_map = {str(p["id"]): p for p in raw_pos}

        num_days = calendar.monthrange(merged_cfg["year"], merged_cfg["month"])[1]
        sd = legacy.date(merged_cfg["year"], merged_cfg["month"], 1)
        ed = legacy.date(merged_cfg["year"], merged_cfg["month"], num_days)
        raw_txns = client.transactions(sd, ed)

        txns_by_emp = legacy.defaultdict(list)
        for t in raw_txns:
            ec = str(t.get("emp_code", ""))
            if ec:
                txns_by_emp[ec].append(t)

        user_weekoffs = legacy.load_user_weekoffs()
        emp_rows = []
        unknown_depts = set()
        for emp in raw_emps:
            ec = str(emp.get("emp_code", emp.get("id", "")))
            dept_name = legacy._resolve(emp, "department", ["dept_name", "name"], depts_map) or "General"
            desig = legacy._resolve(emp, "position", ["position_name", "name"], pos_map)
            rule = legacy._get_rule(dept_name)
            if dept_name not in legacy.DEPT_RULES:
                unknown_depts.add(dept_name)

            weekly_off_days = legacy.employee_weekly_off_days(user_weekoffs, ec)
            effective_rule = {**rule, "weekly_off_days": weekly_off_days}
            calc = legacy.AttendanceCalculator(dept_name, effective_rule)
            att, od, oh = calc.compute(txns_by_emp.get(ec, []), merged_cfg["month"], merged_cfg["year"])
            summ = calc.summarize(att, od, oh)
            emp_rows.append(
                {
                    "emp_code": ec,
                    "name": legacy._name(emp),
                    "designation": desig,
                    "dept": dept_name,
                    "wo_label": legacy.wo_label_for_employee(
                        user_weekoffs, ec, weekly_off_days
                    ),
                    "attendance": att,
                    "ot_days": od,
                    "ot_hours": oh,
                    "summary": summ,
                }
            )

        if unknown_depts:
            print(
                "\nWARN  Departments not in DEPT_RULES (default rules used): "
                f"{', '.join(sorted(unknown_depts))}\n"
            )

        legacy.ReportGenerator(merged_cfg).generate(emp_rows, output_path)
        print(f"Done  ->  {output_path}")

    _, logs = _run_with_capture(_do_report)
    return output_path, logs
