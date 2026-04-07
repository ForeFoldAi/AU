"""Async QThread worker for fetching personnel data from the BioTime API."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from forefold_attendance_gui.api.client import ApiClient, AuthError, PersonnelData


class FetchWorker(QObject):
    """
    Run in a QThread; emits `finished` with parsed data or `failed` with an
    error message.
    """
    finished = Signal(object)   # PersonnelData
    failed   = Signal(str)
    progress = Signal(str)      # status messages for the UI

    def __init__(self, email: str, password: str, company: str = "auinfocity"):
        super().__init__()
        self._email    = email
        self._password = password
        self._company  = company

    def run(self):
        try:
            client = ApiClient(self._email, self._password, self._company)

            self.progress.emit("Authenticating…")
            client.authenticate()

            self.progress.emit("Fetching employees…")
            employees = client.get_employees()

            self.progress.emit("Fetching departments…")
            departments = client.get_departments()

            self.progress.emit("Fetching positions…")
            positions = client.get_positions()

            self.progress.emit("Fetching areas…")
            areas = client.get_areas()

            self.progress.emit("Fetching locations…")
            locations = client.get_locations()

            data = PersonnelData(
                employees=employees,
                departments=departments,
                positions=positions,
                areas=areas,
                locations=locations,
            )
            self.finished.emit(data)

        except AuthError as exc:
            self.failed.emit(f"Authentication failed: {exc}")
        except Exception as exc:
            self.failed.emit(f"Failed to load data: {exc}")


def start_fetch(
    email: str,
    password: str,
    company: str,
    on_finished,
    on_failed,
    on_progress=None,
    parent: QObject | None = None,
) -> tuple[QThread, FetchWorker]:
    """
    Convenience: create, wire, and start a fetch thread.

    Returns (thread, worker) so the caller can keep references alive.
    """
    thread = QThread(parent)
    worker = FetchWorker(email, password, company)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
    if on_progress:
        worker.progress.connect(on_progress)

    # clean up thread when done
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)

    thread.start()
    return thread, worker
