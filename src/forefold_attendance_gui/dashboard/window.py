"""DashboardWindow – main window shown after successful login."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from forefold_attendance_gui.dashboard.employees.tab import EmployeeTab
from forefold_attendance_gui.dashboard.reports.tab import ReportsTab
from forefold_attendance_gui.weekoff.tab import WeekOffTab

# ── Nav button styles ─────────────────────────────────────────────────────────

_NAV_DEFAULT = """
    QPushButton {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: #64748B;
        font-size: 13px;
        font-weight: 500;
        padding: 0 14px;
        min-height: 60px;
    }
    QPushButton:hover { color: #2563EB; }
"""

_NAV_ACTIVE = """
    QPushButton {
        background: transparent;
        border: none;
        border-bottom: 2px solid #2563EB;
        color: #2563EB;
        font-size: 13px;
        font-weight: 600;
        padding: 0 14px;
        min-height: 60px;
    }
"""


class DashboardWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, email: str, password: str):
        super().__init__()
        self.user_email    = email
        self.user_password = password
        self.setWindowTitle("BioTime Attendance System")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self._status = QStatusBar()
        self._status.showMessage("Ready")
        self.setStatusBar(self._status)

        self._build_ui()
        self._center()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("dashRoot")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Build content pages first (nav buttons reference the stack)
        self._stack   = QStackedWidget()
        self._emp_tab = EmployeeTab(self.user_email, self.user_password)
        self._wo_tab  = WeekOffTab(self.user_email, self.user_password)
        self._rep_tab = ReportsTab(self.user_email, self.user_password, self._status)
        self._stack.addWidget(self._emp_tab)   # page 0
        self._stack.addWidget(self._wo_tab)    # page 1
        self._stack.addWidget(self._rep_tab)   # page 2

        outer.addWidget(self._make_header())
        outer.addWidget(self._stack, 1)

        self.setCentralWidget(root)
        self._switch_page(0)  # activate Employee Management on launch

    def _make_header(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("headerBar")
        bar.setFixedHeight(60)
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        shadow = QGraphicsDropShadowEffect(bar)
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 18))
        bar.setGraphicsEffect(shadow)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 16, 0)
        layout.setSpacing(0)

        # ── Brand ─────────────────────────────────────────────────────────────
        app_name = QLabel("BioTime")
        app_name.setObjectName("appName")
        layout.addWidget(app_name)

        dot = QLabel("·")
        dot.setStyleSheet("color:#2563EB; font-size:20px; font-weight:900; padding:0 6px;")
        layout.addWidget(dot)

        sub = QLabel("Attendance System")
        sub.setStyleSheet("font-size:13px; color:#64748B; font-weight:500;")
        layout.addWidget(sub)

        # ── Inline nav tab buttons — centred between brand and user info ────────
        layout.addStretch(1)
        self._nav_btns: list[QPushButton] = []
        for i, label in enumerate(["Employee Management", "Weekly Off", "Reports"]):
            btn = QPushButton(label)
            btn.setFixedHeight(60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._switch_page(idx))
            layout.addWidget(btn)
            self._nav_btns.append(btn)
        layout.addStretch(1)

        # ── User info + logout ────────────────────────────────────────────────
        user_label = QLabel(f"Logged in as  {self.user_email}")
        user_label.setObjectName("userInfo")
        layout.addWidget(user_label)

        sep = QLabel("|")
        sep.setStyleSheet("color:#CBD5E1; font-size:16px; padding:0 8px;")
        layout.addWidget(sep)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFixedHeight(32)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested)
        layout.addWidget(logout_btn)

        return bar

    # ── Navigation ────────────────────────────────────────────────────────────

    def _switch_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_btns):
            btn.setStyleSheet(_NAV_ACTIVE if i == index else _NAV_DEFAULT)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _center(self):
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )
