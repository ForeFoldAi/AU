"""Application entry-point: LoginWindow + run()."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from forefold_attendance_gui.api.worker import LoginAuthWorker  # noqa: E402
from forefold_attendance_gui.branding import APP_DISPLAY_NAME, public_logo_path  # noqa: E402
from forefold_attendance_gui.constants import BACKEND_COMPANY, PRODUCT_WINDOW_TITLE  # noqa: E402
from forefold_attendance_gui.dashboard.window import DashboardWindow  # noqa: E402
from forefold_attendance_gui.style import app_stylesheet              # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
#  Login Window
# ─────────────────────────────────────────────────────────────────────────────

class LoginWindow(QMainWindow):
    login_success = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setObjectName("loginWindow")
        self.resize(960, 640)
        self.setMinimumSize(480, 420)
        self.setWindowTitle(PRODUCT_WINDOW_TITLE)
        self._login_thread: QThread | None = None
        self._login_worker: LoginAuthWorker | None = None
        self._pending_email = ""
        self._pending_password = ""
        self._login_btn_idle_text = "Sign In"
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - 960) // 2,
            (screen.height() - 640) // 2,
        )
        self._build_ui()
        self._wire_signals()
        self.email_input.setFocus()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("loginRoot")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 40, 36, 40)
        card_layout.setSpacing(0)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)

        # Header
        title = QLabel(PRODUCT_WINDOW_TITLE)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)

        subtitle = QLabel("Sign in to continue")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(title)
        card_layout.addSpacing(6)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(32)

        # Email
        card_layout.addWidget(self._field_label("User ID / Email"))
        card_layout.addSpacing(6)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your user ID or email")
        self.email_input.setFixedHeight(42)
        card_layout.addWidget(self.email_input)
        card_layout.addSpacing(18)

        # Password
        card_layout.addWidget(self._field_label("Password"))
        card_layout.addSpacing(6)

        pass_frame = QFrame()
        pass_frame.setObjectName("passwordFrame")
        pass_frame.setFixedHeight(42)
        pass_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pass_row = QHBoxLayout(pass_frame)
        pass_row.setContentsMargins(0, 0, 0, 0)
        pass_row.setSpacing(0)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("passwordInput")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFrame(False)
        self.password_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.toggle_password = QPushButton("Show")
        self.toggle_password.setObjectName("toggleBtn")
        self.toggle_password.setFixedWidth(46)
        self.toggle_password.setCursor(Qt.PointingHandCursor)
        self.toggle_password.setFocusPolicy(Qt.NoFocus)
        self.toggle_password.clicked.connect(self._toggle_password_visibility)

        pass_row.addWidget(self.password_input)
        pass_row.addWidget(self.toggle_password)
        card_layout.addWidget(pass_frame)
        card_layout.addSpacing(10)

        # Error
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(22)
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(14)

        # Sign In
        self.login_btn = QPushButton(self._login_btn_idle_text)
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setFixedHeight(44)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login_clicked)
        card_layout.addWidget(self.login_btn)

        outer.addWidget(card, alignment=Qt.AlignCenter)
        self.setCentralWidget(root)

    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        return lbl

    # ── Signals ───────────────────────────────────────────────────────────────

    def _wire_signals(self):
        self.email_input.textChanged.connect(self._clear_error)
        self.password_input.textChanged.connect(self._clear_error)
        self.email_input.returnPressed.connect(self._on_login_clicked)
        self.password_input.returnPressed.connect(self._on_login_clicked)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _clear_error(self):
        self.error_label.setText("")

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self._shake()

    def _shake(self):
        from PySide6.QtCore import QTimer
        card = self.centralWidget().layout().itemAt(0).widget()
        origin = card.pos()
        offsets = [-8, 8, -6, 6, -4, 4, 0]

        def _step(i=0):
            if i < len(offsets):
                card.move(origin.x() + offsets[i], origin.y())
                QTimer.singleShot(40, lambda: _step(i + 1))

        _step()

    def _on_login_clicked(self):
        email    = self.email_input.text().strip()
        password = self.password_input.text()

        if not email:
            self._show_error("User ID / Email is required.")
            self.email_input.setFocus()
            return
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            self._show_error("Enter a valid email address.")
            self.email_input.setFocus()
            return
        if not password:
            self._show_error("Password is required.")
            self.password_input.setFocus()
            return

        if self._login_thread is not None and self._login_thread.isRunning():
            return

        self._pending_email = email
        self._pending_password = password
        self._set_login_busy(True)
        self._login_thread = QThread(self)
        self._login_worker = LoginAuthWorker(email, password, BACKEND_COMPANY)
        self._login_worker.moveToThread(self._login_thread)
        self._login_thread.started.connect(self._login_worker.run)
        self._login_worker.finished.connect(self._on_login_auth_ok)
        self._login_worker.failed.connect(self._on_login_auth_failed)
        self._login_worker.finished.connect(self._cleanup_login_thread)
        self._login_worker.failed.connect(self._cleanup_login_thread)
        self._login_thread.start()

    def _on_login_auth_ok(self):
        self._set_login_busy(False)
        self.login_success.emit(self._pending_email, self._pending_password)

    def _on_login_auth_failed(self, _message: str):
        self._set_login_busy(False)
        self._show_error("Invalid email or password.")

    def _cleanup_login_thread(self):
        if self._login_thread:
            self._login_thread.quit()
            self._login_thread.wait(8000)
        self._login_thread = None
        self._login_worker = None

    def _set_login_busy(self, busy: bool):
        self.login_btn.setEnabled(not busy)
        self.login_btn.setText("Signing in…" if busy else self._login_btn_idle_text)
        self.email_input.setEnabled(not busy)
        self.password_input.setEnabled(not busy)
        self.toggle_password.setEnabled(not busy)
        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

    def _toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password.setText("Show")


# ─────────────────────────────────────────────────────────────────────────────
#  Application entry-point
# ─────────────────────────────────────────────────────────────────────────────

def run():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
    app.setApplicationName(APP_DISPLAY_NAME)
    _lp = public_logo_path()
    if _lp:
        app.setWindowIcon(QIcon(str(_lp)))
    app.setStyleSheet(app_stylesheet())

    font = QFont()
    font.setPointSize(10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    login = LoginWindow()
    dashboard: DashboardWindow | None = None

    def _open_dashboard(email: str, password: str):
        nonlocal dashboard
        login.hide()
        dashboard = DashboardWindow(email, password)
        dashboard.logout_requested.connect(_back_to_login)
        dashboard.show()
        dashboard.raise_()
        dashboard.activateWindow()

    def _back_to_login():
        if dashboard:
            dashboard.close()
        login.email_input.clear()
        login.password_input.clear()
        login.error_label.clear()
        login.show()
        login.raise_()
        login.activateWindow()
        login.email_input.setFocus()

    login.login_success.connect(_open_dashboard)
    login.show()
    login.raise_()
    login.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
