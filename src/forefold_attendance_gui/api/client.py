"""BioTime API client — authentication + personnel endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests

# Both auth and personnel are on the same HTTPS host
_PERSONNEL_BASE = "https://auinfocity.itimedev.minervaiot.com"
_AUTH_BASE      = "https://auinfocity.itimedev.minervaiot.com"

_PAGE_SIZE = 100
_TIMEOUT   = 30   # seconds per request


# ─────────────────────────────────────────────────────────────────────────────
#  Auth error
# ─────────────────────────────────────────────────────────────────────────────

class AuthError(Exception):
    pass


# ─────────────────────────────────────────────────────────────────────────────
#  Raw API result containers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PersonnelData:
    """All personnel data fetched in one go."""
    employees:   list[dict] = field(default_factory=list)
    departments: list[dict] = field(default_factory=list)
    positions:   list[dict] = field(default_factory=list)
    areas:       list[dict] = field(default_factory=list)
    locations:   list[dict] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  Client
# ─────────────────────────────────────────────────────────────────────────────

class ApiClient:
    """
    Thin wrapper around the BioTime Cloud REST API.

    Usage::

        client = ApiClient(email, password, company)
        client.authenticate()          # raises AuthError on failure
        data = client.fetch_all()      # returns PersonnelData
    """

    _AUTH_ATTEMPTS = [
        ("jwt-api-token-auth",   lambda e, p, c: {"company": c, "email": e, "password": p}, "JWT"),
        ("api-token-auth",       lambda e, p, c: {"company": c, "email": e, "password": p}, "Token"),
        ("staff-jwt-api-token-auth", lambda e, p, c: {"company": c, "username": e, "password": p}, "JWT"),
        ("staff-api-token-auth", lambda e, p, c: {"username": e, "password": p}, "Token"),
        ("api-token-auth",       lambda e, p, c: {"email": e, "password": p}, "Token"),
    ]

    def __init__(self, email: str, password: str, company: str = "auinfocity"):
        self._email   = email
        self._password = password
        self._company  = company
        self._token: str | None = None
        self._scheme: str = "Token"

    # ── Authentication ────────────────────────────────────────────────────────

    def authenticate(self) -> None:
        """Try each auth endpoint in order; raise AuthError if all fail."""
        last_error = ""
        for path, payload_fn, scheme in self._AUTH_ATTEMPTS:
            url = f"{_AUTH_BASE}/{path}/"
            payload = payload_fn(self._email, self._password, self._company)
            try:
                r = requests.post(url, json=payload, timeout=_TIMEOUT)
                if r.ok:
                    data = r.json()
                    tok = data.get("token") or data.get("access") or data.get("jwt")
                    if tok:
                        self._token = tok
                        self._scheme = scheme
                        return
                else:
                    last_error = f"HTTP {r.status_code}: {r.text[:200]}"
            except requests.RequestException as exc:
                last_error = str(exc)

        raise AuthError(f"Authentication failed. Last error: {last_error}")

    # ── Bulk fetch ────────────────────────────────────────────────────────────

    def fetch_all(self) -> PersonnelData:
        """Fetch employees, departments, positions, areas, and locations."""
        return PersonnelData(
            employees   = self.get_employees(),
            departments = self.get_departments(),
            positions   = self.get_positions(),
            areas       = self.get_areas(),
            locations   = self.get_locations(),
        )

    # ── Individual endpoints ──────────────────────────────────────────────────

    def get_employees(self) -> list[dict]:
        return self._get_all(f"{_PERSONNEL_BASE}/personnel/api/employees/")

    def get_departments(self) -> list[dict]:
        return self._get_all(f"{_PERSONNEL_BASE}/personnel/api/departments/")

    def get_positions(self) -> list[dict]:
        return self._get_all(f"{_PERSONNEL_BASE}/personnel/api/positions/")

    def get_areas(self) -> list[dict]:
        try:
            return self._get_all(f"{_PERSONNEL_BASE}/personnel/api/areas/")
        except requests.HTTPError:
            return []

    def get_locations(self) -> list[dict]:
        try:
            return self._get_all(f"{_PERSONNEL_BASE}/personnel/api/locations/")
        except requests.HTTPError:
            return []

    # ── Internal ──────────────────────────────────────────────────────────────

    def _headers(self) -> dict:
        if not self._token:
            raise AuthError("Not authenticated. Call authenticate() first.")
        return {
            "Authorization": f"{self._scheme} {self._token}",
            "Content-Type":  "application/json",
        }

    def _get_all(self, url: str, params: dict | None = None) -> list[dict]:
        """Fetch all pages from a paginated endpoint."""
        params = dict(params or {})
        params.setdefault("page_size", _PAGE_SIZE)
        params["page"] = 1
        results: list[dict] = []

        while True:
            r = requests.get(url, headers=self._headers(), params=params, timeout=60)
            r.raise_for_status()
            body: dict[str, Any] = r.json()
            page_items = body.get("data") or body.get("results") or []
            results.extend(page_items)
            if not body.get("next"):
                break
            params["page"] += 1

        return results

    # ── Lookup helpers (static) ───────────────────────────────────────────────

    @staticmethod
    def build_dept_map(departments: list[dict]) -> dict[str, str]:
        """id → dept_name"""
        out: dict[str, str] = {}
        for d in departments:
            name = d.get("dept_name") or d.get("name") or ""
            out[str(d.get("id", ""))] = name
        return out

    @staticmethod
    def build_position_map(positions: list[dict]) -> dict[str, str]:
        """id → position_name"""
        out: dict[str, str] = {}
        for p in positions:
            name = p.get("position_name") or p.get("name") or ""
            out[str(p.get("id", ""))] = name
        return out

    @staticmethod
    def build_area_map(areas: list[dict]) -> dict[str, str]:
        """id → area_name"""
        out: dict[str, str] = {}
        for a in areas:
            name = a.get("area_name") or a.get("name") or ""
            out[str(a.get("id", ""))] = name
        return out

    @staticmethod
    def resolve_field(obj: dict, key: str, field_keys: list[str], lookup: dict[str, str]) -> str:
        """
        Resolve a FK field that may be:
        - a nested dict   → check field_keys inside it
        - a plain id      → look up in `lookup`
        - a string itself → return as-is
        """
        val = obj.get(key)
        if isinstance(val, dict):
            for fk in field_keys:
                if val.get(fk):
                    return str(val[fk])
            # fall through to id lookup
            val = val.get("id")
        if val is not None:
            found = lookup.get(str(val))
            if found:
                return found
        # last resort: look for direct flat keys on the object
        for fk in field_keys:
            if obj.get(fk):
                return str(obj[fk])
        return ""

    @staticmethod
    def employee_display_name(emp: dict) -> str:
        fn = (emp.get("first_name") or "").strip()
        ln = (emp.get("last_name")  or "").strip()
        full = f"{fn} {ln}".strip()
        return full or emp.get("emp_name") or emp.get("name") or f"EMP-{emp.get('emp_code', '?')}"
