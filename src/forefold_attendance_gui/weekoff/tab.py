"""Employee management tab — weekly off assignment and related employee grid."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QEvent,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    QThread,
)
from PySide6.QtGui import QColor, QPainterPath, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QFrame,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from forefold_attendance_gui.api.client import PersonnelData
from forefold_attendance_gui.api.worker import FetchWorker, start_fetch
from forefold_attendance_gui.dashboard.employees.model import Employee, employees_from_api
from forefold_attendance_gui.dashboard.imports.tab import ImportsPanel
from forefold_attendance_gui.imports_store import enrich_employees_from_imports
from forefold_attendance_gui.weekoff import store

_BACKEND_COMPANY = "auinfocity"

DAYS      = store.DAYS  # ["Monday", ..., "Sunday"]
DAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ── Table columns ──────────────────────────────────────────────────────────────
#  Emp ID | Name | Area | Department | Shift details | Shift time table | Week off | Mon … Sun
COL_EMP_ID         = 0
COL_NAME           = 1
COL_AREA           = 2
COL_DEPT           = 3
COL_SHIFT          = 4
COL_SHIFT_TIMING   = 5
COL_WEEKOFF        = 6
COL_DAY_FIRST      = 7
COL_DAY_LAST       = COL_DAY_FIRST + 6

_DAY_HEADERS = (
    [
        "Employee ID",
        "Name",
        "Area",
        "Department",
        "Shift details",
        "Shift time table",
        "Week off",
    ]
    + DAYS_SHORT
)

_PAGE_LOADING = 0
_PAGE_ERROR   = 1
_PAGE_TABLE   = 2

# Repo root (…/exe) so `attendance_report` can be imported for department rules.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_attendance_report = None


def _attendance_report_mod():
    global _attendance_report
    if _attendance_report is None:
        import attendance_report as ar  # noqa: PLC0415

        _attendance_report = ar
    return _attendance_report


def _employee_weekly_off_assignable(emp: Employee) -> bool:
    """False for Security and any dept whose rules have no weekly-off days."""
    rule = _attendance_report_mod()._get_rule(emp.department or "")
    return bool(rule.get("weekly_off_days"))


def _employee_from_proxy_index(index: QModelIndex) -> Employee | None:
    m = index.model()
    if isinstance(m, QSortFilterProxyModel):
        src = m.mapToSource(index)
        if not src.isValid():
            return None
        sm = m.sourceModel()
        return sm.data(sm.index(src.row(), 0), Qt.ItemDataRole.UserRole)
    return m.data(m.index(index.row(), 0), Qt.ItemDataRole.UserRole)


# ─────────────────────────────────────────────────────────────────────────────
#  Table model
# ─────────────────────────────────────────────────────────────────────────────

class _WeekOffTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._employees: list[Employee] = []
        self._weekoffs: dict[str, str | None] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._employees)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_DAY_HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        emp = self._employees[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == COL_EMP_ID:  return emp.emp_id
            if col == COL_NAME:    return emp.name
            if col == COL_AREA:    return emp.area
            if col == COL_DEPT:    return emp.department
            if col == COL_SHIFT:   return emp.display_shift
            if col == COL_SHIFT_TIMING:
                return emp.shift_timing or "—"
            if col == COL_WEEKOFF:
                if not _employee_weekly_off_assignable(emp):
                    return "—"
                return self._weekoffs.get(emp.emp_id) or "—"
            # Day columns → True if this is the employee's weekly-off day
            if COL_DAY_FIRST <= col <= COL_DAY_LAST:
                if not _employee_weekly_off_assignable(emp):
                    return False
                day_name = DAYS[col - COL_DAY_FIRST]
                return self._weekoffs.get(emp.emp_id) == day_name

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if COL_DAY_FIRST <= col <= COL_DAY_LAST:
                return Qt.AlignmentFlag.AlignCenter
            if col in (
                COL_EMP_ID,
                COL_NAME,
                COL_AREA,
                COL_DEPT,
                COL_SHIFT_TIMING,
            ):
                return Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        if role == Qt.ItemDataRole.ForegroundRole:
            return QColor("#1E293B")

        if role == Qt.ItemDataRole.UserRole:
            return emp

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = super().flags(index)
        col = index.column()
        if COL_DAY_FIRST <= col <= COL_DAY_LAST:
            emp = self._employees[index.row()]
            if not _employee_weekly_off_assignable(emp):
                return base & ~Qt.ItemFlag.ItemIsEditable
            return base | Qt.ItemFlag.ItemIsEditable
        # COL_WEEKOFF and info columns are read-only
        return base & ~Qt.ItemFlag.ItemIsEditable

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False
        col = index.column()
        if role != Qt.ItemDataRole.EditRole or not (COL_DAY_FIRST <= col <= COL_DAY_LAST):
            return False

        emp = self._employees[index.row()]
        if not _employee_weekly_off_assignable(emp):
            return False
        day_name = DAYS[col - COL_DAY_FIRST]
        current  = self._weekoffs.get(emp.emp_id)

        # Toggle: clicking an already-selected day clears it
        self._weekoffs[emp.emp_id] = None if current == day_name else day_name

        # Refresh Weekly Off text column + all day radio columns for this row
        self.dataChanged.emit(
            self.index(index.row(), COL_WEEKOFF),
            self.index(index.row(), COL_DAY_LAST),
            [Qt.ItemDataRole.DisplayRole],
        )
        return True

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return _DAY_HEADERS[section]
            if role == Qt.ItemDataRole.TextAlignmentRole:
                if section in (
                    COL_EMP_ID,
                    COL_NAME,
                    COL_AREA,
                    COL_DEPT,
                    COL_SHIFT_TIMING,
                    COL_WEEKOFF,
                ) or COL_DAY_FIRST <= section <= COL_DAY_LAST:
                    return Qt.AlignmentFlag.AlignCenter
                return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        return None

    # ── Public API ────────────────────────────────────────────────────────────

    def reload(self, employees: list[Employee], weekoffs: dict[str, str | None]) -> None:
        self.beginResetModel()
        self._employees = list(employees)
        wo = dict(weekoffs)
        for e in self._employees:
            if not _employee_weekly_off_assignable(e):
                wo.pop(e.emp_id, None)
        self._weekoffs = wo
        self.endResetModel()

    def employee_at(self, row: int) -> Employee | None:
        return self._employees[row] if 0 <= row < len(self._employees) else None

    def get_weekoff(self, emp_id: str) -> str | None:
        return self._weekoffs.get(emp_id)

    def get_weekoffs(self) -> dict[str, str | None]:
        out = dict(self._weekoffs)
        for e in self._employees:
            if not _employee_weekly_off_assignable(e):
                out.pop(e.emp_id, None)
        return out

    def set_day_for_rows(self, rows: list[int], day: str | None) -> None:
        """Set a specific day (or None) for multiple source rows."""
        for row in rows:
            if 0 <= row < len(self._employees):
                emp = self._employees[row]
                if not _employee_weekly_off_assignable(emp):
                    continue
                self._weekoffs[emp.emp_id] = day
        if rows:
            first = min(rows)
            last  = max(rows)
            # Refresh Weekly Off text column + all day radio columns
            self.dataChanged.emit(
                self.index(first, COL_WEEKOFF),
                self.index(last,  COL_DAY_LAST),
                [Qt.ItemDataRole.DisplayRole],
            )


# ─────────────────────────────────────────────────────────────────────────────
#  Filter proxy
# ─────────────────────────────────────────────────────────────────────────────

class _FilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search = ""
        self._area   = "All Areas"
        self._dept   = "All Departments"
        self._shift  = "All Shifts"

    def set_search(self, text: str) -> None:
        self._search = text.strip().lower()
        self.invalidateFilter()

    def set_area(self, area: str) -> None:
        self._area = area
        self.invalidateFilter()

    def set_dept(self, dept: str) -> None:
        self._dept = dept
        self.invalidateFilter()

    def set_shift(self, shift: str) -> None:
        self._shift = shift
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        emp: Employee | None = self.sourceModel().data(
            self.sourceModel().index(source_row, 0), Qt.ItemDataRole.UserRole
        )
        if emp is None:
            return True
        ds = emp.display_shift
        st = (emp.shift_timing or "").lower()
        if self._search and self._search not in (
            emp.emp_id.lower()
            + emp.name.lower()
            + emp.department.lower()
            + emp.area.lower()
            + ds.lower()
            + (emp.import_shift_name or "").lower()
            + st
        ):
            return False
        if self._area != "All Areas" and emp.area != self._area:
            return False
        if self._dept != "All Departments" and emp.department != self._dept:
            return False
        if self._shift != "All Shifts" and ds != self._shift:
            return False
        return True


# ─────────────────────────────────────────────────────────────────────────────
#  Weekly Off pill delegate  (COL_WEEKOFF — text summary column)
# ─────────────────────────────────────────────────────────────────────────────

class _WeekOffPillDelegate(QStyledItemDelegate):
    _ASSIGNED_BG = QColor("#EFF6FF")
    _ASSIGNED_FG = QColor("#2563EB")
    _NONE_BG     = QColor("#F8FAFC")
    _NONE_FG     = QColor("#94A3B8")

    def paint(self, painter, option: QStyleOptionViewItem, index: QModelIndex):
        from PySide6.QtCore import QRect

        value    = index.data(Qt.ItemDataRole.DisplayRole) or "—"
        assigned = value != "—"
        bg = self._ASSIGNED_BG if assigned else self._NONE_BG
        fg = self._ASSIGNED_FG if assigned else self._NONE_FG

        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        pill_w = max(75, len(value) * 8 + 24)
        pill_h = 22
        x    = option.rect.x() + (option.rect.width() - pill_w) // 2
        y    = option.rect.y() + (option.rect.height() - pill_h) // 2
        pill = QRect(x, y, pill_w, pill_h)

        path = QPainterPath()
        path.addRoundedRect(pill.x(), pill.y(), pill.width(), pill.height(), 11, 11)
        painter.fillPath(path, bg)

        painter.setPen(fg)
        f = painter.font()
        f.setPointSize(8)
        f.setBold(assigned)
        painter.setFont(f)
        painter.drawText(pill, Qt.AlignCenter, value)
        painter.restore()


# ─────────────────────────────────────────────────────────────────────────────
#  Radio-button cell delegate
# ─────────────────────────────────────────────────────────────────────────────

class _RadioDelegate(QStyledItemDelegate):
    """Draws a radio-button circle in each day column cell.

    A left-click toggles the selection for the clicked row (or all selected
    rows if the row is part of a multi-row selection).
    """

    _CHECKED_FILL   = QColor("#2563EB")
    _CHECKED_BORDER = QColor("#1D4ED8")
    _EMPTY_BORDER   = QColor("#CBD5E1")
    _HOVER_BORDER   = QColor("#93C5FD")

    def __init__(self, table: QTableView, parent=None):
        super().__init__(parent)
        self._table = table

    def createEditor(self, parent, option, index):
        return None  # never show an editor widget — clicks handled in editorEvent

    def paint(self, painter, option: QStyleOptionViewItem, index: QModelIndex):
        from PySide6.QtWidgets import QStyle
        from PySide6.QtGui import QPen

        emp = _employee_from_proxy_index(index)
        if emp is not None and not _employee_weekly_off_assignable(emp):
            painter.save()
            painter.setRenderHint(painter.RenderHint.Antialiasing)
            selected = bool(option.state & QStyle.StateFlag.State_Selected)
            if selected:
                painter.fillRect(option.rect, QColor("#EFF6FF"))
            elif option.rect.top() // 46 % 2 == 1:
                painter.fillRect(option.rect, QColor("#F8FAFC"))
            else:
                painter.fillRect(option.rect, QColor("#ffffff"))
            painter.restore()
            return

        checked = bool(index.data(Qt.ItemDataRole.DisplayRole))

        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        # Background (respect selection / alternating)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if selected:
            painter.fillRect(option.rect, QColor("#EFF6FF"))
        elif option.rect.top() // 46 % 2 == 1:
            painter.fillRect(option.rect, QColor("#F8FAFC"))
        else:
            painter.fillRect(option.rect, QColor("#ffffff"))

        # Circle geometry — centred in cell
        r  = 7
        cx = option.rect.center().x()
        cy = option.rect.center().y()

        if checked:
            # Filled blue circle
            path = QPainterPath()
            path.addEllipse(cx - r, cy - r, r * 2, r * 2)
            painter.fillPath(path, self._CHECKED_FILL)
            painter.setPen(self._CHECKED_BORDER)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            # White tick mark — drawn as two line segments (no font dependency)
            pen = QPen(QColor("#ffffff"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(int(cx - 3), int(cy + 1), int(cx - 1), int(cy + 3))
            painter.drawLine(int(cx - 1), int(cy + 3), int(cx + 4), int(cy - 3))
        else:
            # Empty circle with light border
            hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
            border  = self._HOVER_BORDER if hovered else self._EMPTY_BORDER
            painter.setPen(border)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        painter.restore()

    def editorEvent(
        self,
        event: QEvent,
        model,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        if event.type() != QEvent.Type.MouseButtonRelease:
            return False

        col = index.column()
        if not (COL_DAY_FIRST <= col <= COL_DAY_LAST):
            return False

        emp_here = _employee_from_proxy_index(index)
        if emp_here is not None and not _employee_weekly_off_assignable(emp_here):
            return False

        # Determine which source rows to update
        sel_proxy_rows = self._table.selectionModel().selectedRows()
        clicked_in_sel = any(r.row() == index.row() for r in sel_proxy_rows)

        if clicked_in_sel and len(sel_proxy_rows) > 1:
            # Bulk: apply same day to all selected rows
            day_name = DAYS[col - COL_DAY_FIRST]
            src_model = model.sourceModel()
            src_rows = [model.mapToSource(r).row() for r in sel_proxy_rows]
            src_rows = [
                r
                for r in src_rows
                if (e := src_model.employee_at(r)) is not None
                and _employee_weekly_off_assignable(e)
            ]
            if not src_rows:
                return True
            # If all already have this day → clear; otherwise set
            all_same = all(src_model.get_weekoff(src_model.employee_at(r).emp_id) == day_name
                           for r in src_rows if src_model.employee_at(r))
            src_model.set_day_for_rows(src_rows, None if all_same else day_name)
        else:
            model.setData(index, None, Qt.ItemDataRole.EditRole)

        return True

    def sizeHint(self, option, index):
        sh = super().sizeHint(option, index)
        sh.setWidth(46)
        return sh


# ─────────────────────────────────────────────────────────────────────────────
#  Loading / Error panes
# ─────────────────────────────────────────────────────────────────────────────

class _LoadingPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(12)
        lbl = QLabel("Loading…")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #64748B;")
        self._sub = QLabel("")
        self._sub.setAlignment(Qt.AlignCenter)
        self._sub.setStyleSheet("font-size: 10pt; color: #94A3B8;")
        lay.addWidget(lbl)
        lay.addWidget(self._sub)

    def set_status(self, msg: str) -> None:
        self._sub.setText(msg)


class _ErrorPane(QWidget):
    def __init__(self, on_retry, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(16)
        icon = QLabel("⚠")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 36px;")
        self._msg = QLabel("Failed to load employee data.")
        self._msg.setAlignment(Qt.AlignCenter)
        self._msg.setWordWrap(True)
        self._msg.setStyleSheet("font-size: 11pt; color: #DC2626;")
        retry = QPushButton("Retry")
        retry.setObjectName("primaryButton")
        retry.setFixedWidth(120)
        retry.clicked.connect(on_retry)
        lay.addWidget(icon)
        lay.addWidget(self._msg)
        lay.addWidget(retry, alignment=Qt.AlignCenter)

    def set_message(self, msg: str) -> None:
        self._msg.setText(msg)


# ─────────────────────────────────────────────────────────────────────────────
#  WeekOffTab
# ─────────────────────────────────────────────────────────────────────────────

class WeekOffTab(QWidget):
    def __init__(self, email: str, password: str, parent=None):
        super().__init__(parent)
        self._email    = email
        self._password = password
        self._all_employees: list[Employee] = []
        self._thread: QThread | None = None
        self._worker: FetchWorker | None = None

        self._build_ui()
        self._fetch_data()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Header (single row: title | Import | Refresh | Save) ───────────────
        hdr_host = QWidget()
        hdr = QHBoxLayout(hdr_host)
        hdr.setSpacing(16)
        hdr.setContentsMargins(0, 0, 0, 10)

        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel("Employee management")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "Click a day cell to assign a weekly off. "
            "Select multiple rows then click a day to bulk-assign. "
            "Security (no weekly off in rules) has no day selectors."
        )
        subtitle.setObjectName("sectionSubtitle")
        col.addWidget(title)
        col.addWidget(subtitle)
        hdr.addLayout(col, 1)

        self._imports_panel = ImportsPanel(self, embedded=True)
        hdr.addWidget(self._imports_panel, 0, Qt.AlignmentFlag.AlignVCenter)

        _btn_h = 36
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("secondaryButton")
        self._refresh_btn.setFixedSize(90, _btn_h)
        self._refresh_btn.clicked.connect(self._fetch_data)
        self._save_btn = QPushButton("Save Changes")
        self._save_btn.setObjectName("primaryButton")
        self._save_btn.setFixedSize(130, _btn_h)
        self._save_btn.clicked.connect(self._save_data)
        wrap_btns = QWidget()
        btn_row = QHBoxLayout(wrap_btns)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(8)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addWidget(self._save_btn)
        hdr.addWidget(wrap_btns, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(hdr_host)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self._search = QLineEdit()
        self._search.setObjectName("searchInput")
        self._search.setPlaceholderText(
            "Search by name, ID, department, area, shift details, shift time table…"
        )
        self._search.setFixedHeight(36)
        toolbar.addWidget(self._search, 1)

        filters = QHBoxLayout()
        filters.setSpacing(8)
        for label, combo_attr in (
            ("Area", "_area_filter"),
            ("Department", "_dept_filter"),
            ("Shift details", "_shift_filter"),
        ):
            lab = QLabel(label)
            lab.setStyleSheet("color:#64748B; font-size:12px;")
            cb = QComboBox()
            cb.setObjectName("filterCombo")
            cb.setFixedHeight(36)
            cb.setMinimumWidth(150)
            setattr(self, combo_attr, cb)
            filters.addWidget(lab)
            filters.addWidget(cb)
        toolbar.addLayout(filters)
        root.addLayout(toolbar)

        # ── Table ─────────────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._loading_pane = _LoadingPane()
        self._error_pane   = _ErrorPane(on_retry=self._fetch_data)

        self._model = _WeekOffTableModel()
        self._proxy = _FilterProxy()
        self._proxy.setSourceModel(self._model)
        self._search.textChanged.connect(self._proxy.set_search)
        self._area_filter.currentTextChanged.connect(self._proxy.set_area)
        self._dept_filter.currentTextChanged.connect(self._proxy.set_dept)
        self._shift_filter.currentTextChanged.connect(self._proxy.set_shift)
        self._proxy.modelReset.connect(self._update_count)
        self._proxy.rowsInserted.connect(self._update_count)
        self._proxy.rowsRemoved.connect(self._update_count)
        self._model.dataChanged.connect(self._update_count)

        self.table = QTableView()
        self.table.setObjectName("employeeTable")
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        pal = self.table.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#F8FAFC"))
        self.table.setPalette(pal)
        self.table.setModel(self._proxy)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setMouseTracking(True)

        # Weekly Off text column — pill delegate
        self._pill_delegate  = _WeekOffPillDelegate(self.table)
        self.table.setItemDelegateForColumn(COL_WEEKOFF, self._pill_delegate)

        # Attach radio delegate to all day columns
        self._radio_delegate = _RadioDelegate(self.table, self.table)
        for col_idx in range(COL_DAY_FIRST, COL_DAY_LAST + 1):
            self.table.setItemDelegateForColumn(col_idx, self._radio_delegate)

        hh = self.table.horizontalHeader()
        # Extra width goes to Name; day columns stay equal (no gap between Sat and Sun).
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(COL_EMP_ID, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        hh.setSectionResizeMode(COL_AREA, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_DEPT, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_SHIFT, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_SHIFT_TIMING, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_WEEKOFF, QHeaderView.Fixed)
        hh.resizeSection(COL_WEEKOFF, 100)
        for col_idx in range(COL_DAY_FIRST, COL_DAY_LAST + 1):
            hh.setSectionResizeMode(col_idx, QHeaderView.Fixed)
            hh.resizeSection(col_idx, 52)

        self.table.verticalHeader().setDefaultSectionSize(46)

        self._stack.addWidget(self._loading_pane)  # 0
        self._stack.addWidget(self._error_pane)    # 1
        self._stack.addWidget(self.table)           # 2
        root.addWidget(self._stack, 1)

        # ── Footer ────────────────────────────────────────────────────────────
        self._count_label = QLabel("")
        self._count_label.setObjectName("sectionSubtitle")
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
        self._all_employees = enrich_employees_from_imports(employees_from_api(data))
        self._refresh_btn.setEnabled(True)
        weekoffs = store.load()
        self._model.reload(self._all_employees, weekoffs)
        self._rebuild_filter_combos()
        self._update_count()
        self._stack.setCurrentIndex(_PAGE_TABLE)

    def _on_fetch_error(self, message: str):
        self._refresh_btn.setEnabled(True)
        self._error_pane.set_message(message)
        self._stack.setCurrentIndex(_PAGE_ERROR)

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save_data(self):
        try:
            store.save(self._model.get_weekoffs())
            msg = QMessageBox(self)
            msg.setWindowTitle("Saved")
            msg.setText("Weekly off assignments saved successfully.")
            msg.setIcon(QMessageBox.Information)
            msg.exec()
        except Exception as exc:
            msg = QMessageBox(self)
            msg.setWindowTitle("Save Failed")
            msg.setText(f"Could not save: {exc}")
            msg.setIcon(QMessageBox.Critical)
            msg.exec()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _rebuild_filter_combos(self):
        areas = sorted({e.area for e in self._all_employees})
        depts = sorted({e.department for e in self._all_employees})
        shifts = sorted(
            {e.display_shift for e in self._all_employees if e.display_shift != "—"}
        )

        def _fill(cb: QComboBox, all_label: str, items: list[str]) -> None:
            cb.blockSignals(True)
            cb.clear()
            cb.addItem(all_label)
            cb.addItems(items)
            cb.blockSignals(False)

        _fill(self._area_filter, "All Areas", areas)
        _fill(self._dept_filter, "All Departments", depts)
        _fill(self._shift_filter, "All Shifts", shifts)

    def _update_count(self):
        shown      = self._proxy.rowCount()
        total      = len(self._all_employees)
        weekoffs   = self._model.get_weekoffs()
        assignable = [e for e in self._all_employees if _employee_weekly_off_assignable(e)]
        assigned   = sum(1 for e in assignable if weekoffs.get(e.emp_id))
        unassigned = len(assignable) - assigned
        count      = f"Showing {shown} of {total}" if shown != total else str(total)
        self._count_label.setText(
            f"{count} employees  ·  Assigned: {assigned}  ·  Unassigned: {unassigned}"
        )
