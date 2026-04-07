"""Employee Management tab — live data from BioTime API."""

from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt, QThread
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from forefold_attendance_gui.api.worker import FetchWorker, start_fetch
from forefold_attendance_gui.api.client import PersonnelData
from forefold_attendance_gui.dashboard.employees.model import (
    COL_STATUS,
    Employee,
    EmployeeTableModel,
    employees_from_api,
)

_BACKEND_COMPANY = "auinfocity"

_PAGE_LOADING = 0
_PAGE_ERROR   = 1
_PAGE_TABLE   = 2


# ─────────────────────────────────────────────────────────────────────────────
#  Loading / Error panes
# ─────────────────────────────────────────────────────────────────────────────

class _LoadingPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        self._spinner = QLabel("Loading…")
        self._spinner.setAlignment(Qt.AlignCenter)
        self._spinner.setStyleSheet("font-size:16px; font-weight:600; color:#64748B;")
        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet("font-size:10pt; color:#94A3B8;")
        layout.addWidget(self._spinner)
        layout.addWidget(self._status)

    def set_status(self, msg: str) -> None:
        self._status.setText(msg)


class _ErrorPane(QWidget):
    def __init__(self, on_retry, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        icon = QLabel("⚠")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size:36px;")
        self._msg = QLabel("Failed to load employee data.")
        self._msg.setAlignment(Qt.AlignCenter)
        self._msg.setWordWrap(True)
        self._msg.setStyleSheet("font-size:11pt; color:#DC2626;")
        retry = QPushButton("Retry")
        retry.setObjectName("primaryButton")
        retry.setFixedWidth(120)
        retry.clicked.connect(on_retry)
        layout.addWidget(icon)
        layout.addWidget(self._msg)
        layout.addWidget(retry, alignment=Qt.AlignCenter)

    def set_message(self, msg: str) -> None:
        self._msg.setText(msg)


# ─────────────────────────────────────────────────────────────────────────────
#  Employee Tab
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeTab(QWidget):
    def __init__(self, email: str, password: str, parent=None):
        super().__init__(parent)
        self._email    = email
        self._password = password
        self._all_employees: list[Employee] = []
        self._thread: QThread | None = None
        self._worker: FetchWorker | None = None
        self._build_ui()
        self._fetch_data()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Header row ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr_col = QVBoxLayout()
        hdr_col.setSpacing(4)
        t = QLabel("Employee Management")
        t.setObjectName("sectionTitle")
        s = QLabel("Live data from BioTime Cloud API.")
        s.setObjectName("sectionSubtitle")
        hdr_col.addWidget(t)
        hdr_col.addWidget(s)
        hdr.addLayout(hdr_col, 1)
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("secondaryButton")
        self._refresh_btn.setFixedWidth(100)
        self._refresh_btn.clicked.connect(self._fetch_data)
        hdr.addWidget(self._refresh_btn, alignment=Qt.AlignBottom)
        root.addLayout(hdr)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.search = QLineEdit()
        self.search.setObjectName("searchInput")
        self.search.setPlaceholderText("Search by name, ID, position…")
        self.search.setFixedHeight(36)
        self.search.textChanged.connect(self._apply_filters)

        self.dept_filter = QComboBox()
        self.dept_filter.setObjectName("filterCombo")
        self.dept_filter.setFixedHeight(36)
        self.dept_filter.setMinimumWidth(160)
        self.dept_filter.currentIndexChanged.connect(self._apply_filters)

        self.shift_filter = QComboBox()
        self.shift_filter.setObjectName("filterCombo")
        self.shift_filter.setFixedHeight(36)
        self.shift_filter.setMinimumWidth(180)
        self.shift_filter.currentIndexChanged.connect(self._apply_filters)

        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(self.dept_filter)
        toolbar.addWidget(self.shift_filter)
        root.addLayout(toolbar)

        # ── Stacked: loading / error / table ──────────────────────────────────
        self._stack = QStackedWidget()
        self._loading_pane = _LoadingPane()
        self._error_pane   = _ErrorPane(on_retry=self._fetch_data)

        self._model = EmployeeTableModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.table = QTableView()
        self.table.setObjectName("employeeTable")
        self.table.setModel(self._proxy)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setMinimumSectionSize(70)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Emp ID
        hh.setSectionResizeMode(1, QHeaderView.Stretch)            # Name
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Position
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Department
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Shift
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status (hidden)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.hideColumn(COL_STATUS)

        self._stack.addWidget(self._loading_pane)  # 0
        self._stack.addWidget(self._error_pane)    # 1
        self._stack.addWidget(self.table)           # 2
        root.addWidget(self._stack, 1)

        # ── Footer — count + inline stats ────────────────────────────────────
        self._count_label = QLabel("")
        self._count_label.setObjectName("sectionSubtitle")
        self._model.modelReset.connect(self._update_footer)
        root.addWidget(self._count_label)

    # ── Data fetching ─────────────────────────────────────────────────────────

    def _fetch_data(self):
        if self._thread and self._thread.isRunning():
            return
        self._refresh_btn.setEnabled(False)
        self._stack.setCurrentIndex(_PAGE_LOADING)
        self._loading_pane.set_status("Connecting to BioTime API…")
        self._thread, self._worker = start_fetch(
            email=self._email,
            password=self._password,
            company=_BACKEND_COMPANY,
            on_finished=self._on_data_ready,
            on_failed=self._on_fetch_error,
            on_progress=self._loading_pane.set_status,
            parent=self,
        )

    def _on_data_ready(self, data: PersonnelData):
        self._all_employees = employees_from_api(data)
        self._refresh_btn.setEnabled(True)
        self._rebuild_filter_combos()
        self._apply_filters()
        self._stack.setCurrentIndex(_PAGE_TABLE)

    def _on_fetch_error(self, message: str):
        self._refresh_btn.setEnabled(True)
        self._error_pane.set_message(message)
        self._stack.setCurrentIndex(_PAGE_ERROR)

    # ── Filtering ─────────────────────────────────────────────────────────────

    def _apply_filters(self):
        search    = self.search.text().strip().lower()
        dept_sel  = self.dept_filter.currentText()
        shift_sel = self.shift_filter.currentText()
        filtered  = [
            e for e in self._all_employees
            if _matches(e, search, dept_sel, shift_sel)
        ]
        self._model.reload(filtered)

    def _rebuild_filter_combos(self):
        depts  = sorted({e.department for e in self._all_employees})
        shifts = sorted({e.shift      for e in self._all_employees})
        for combo, all_label, items in (
            (self.dept_filter,  "All Departments", depts),
            (self.shift_filter, "All Shifts",      shifts),
        ):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(all_label)
            combo.addItems(items)
            combo.blockSignals(False)

    # ── Footer ────────────────────────────────────────────────────────────────

    def _update_footer(self):
        shown  = self._model.rowCount()
        total  = len(self._all_employees)
        active = sum(1 for e in self._all_employees if e.status == "Active")
        depts  = len({e.department for e in self._all_employees})
        shifts = len({e.shift      for e in self._all_employees})
        count  = f"Showing {shown} of {total}" if shown != total else str(total)
        self._count_label.setText(
            f"{count} employees  ·  Active: {active}"
            f"  ·  Departments: {depts}  ·  Shifts: {shifts}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Pure filter predicate
# ─────────────────────────────────────────────────────────────────────────────

def _matches(emp: Employee, search: str, dept: str, shift: str) -> bool:
    if search and search not in (
        emp.name.lower() + emp.emp_id.lower() + emp.position.lower()
    ):
        return False
    if dept  != "All Departments" and emp.department != dept:
        return False
    if shift != "All Shifts"      and emp.shift      != shift:
        return False
    return True
