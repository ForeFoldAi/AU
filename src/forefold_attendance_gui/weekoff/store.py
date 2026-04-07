"""Weekly-off assignment store — persists to ~/.forefold/weekoffs.json."""
from __future__ import annotations

import json
from pathlib import Path

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
STORE_PATH = Path.home() / ".forefold" / "weekoffs.json"


def load() -> dict[str, str | None]:
    """Return {emp_id: day_name | None} from disk."""
    if not STORE_PATH.exists():
        return {}
    try:
        with STORE_PATH.open(encoding="utf-8") as f:
            return json.load(f).get("weekoffs", {})
    except Exception:
        return {}


def save(weekoffs: dict[str, str | None]) -> None:
    """Persist {emp_id: day_name | None} to disk."""
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STORE_PATH.open("w", encoding="utf-8") as f:
        json.dump({"weekoffs": weekoffs}, f, indent=2, ensure_ascii=False)


def day_to_index(day_name: str) -> int | None:
    """Convert day name to 0-indexed int (0=Monday … 6=Sunday), or None."""
    try:
        return DAYS.index(day_name)
    except ValueError:
        return None


def validate_weekly_off(
    day: int,
    attendance: list[str],
) -> str:
    """
    Validate a single weekly-off day and return the correct status string.

    Rule: WO is valid only if the employee is Present ("P") on both the
    previous day and the next day. Otherwise the day is treated as Leave.

    Parameters
    ----------
    day        : 0-based index into *attendance* for the day being validated.
    attendance : Full month attendance list. Each element is one of:
                 "P" (Present), "A" (Absent), "WO" (Weekly Off).

    Returns
    -------
    "WO"    — weekly off is valid
    "Leave" — weekly off failed the adjacency check
    """
    prev_present = day > 0 and attendance[day - 1] == "P"
    next_present = day < len(attendance) - 1 and attendance[day + 1] == "P"
    return "WO" if (prev_present and next_present) else "Leave"
