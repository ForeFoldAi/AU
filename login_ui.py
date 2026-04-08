import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QGraphicsDropShadowEffect,
    QSizePolicy, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


# ─────────────────────────────────────────────
#  Stylesheet
# ─────────────────────────────────────────────
STYLESHEET = """
/* ── Window ── */
QMainWindow, #centralWidget {
    background-color: #F1F5F9;
}

/* ── Card ── */
#loginCard {
    background-color: #FFFFFF;
    border-radius: 16px;
}

/* ── Title ── */
#titleLabel {
    font-size: 22px;
    font-weight: 700;
    color: #0F172A;
}

/* ── Subtitle ── */
#subtitleLabel {
    font-size: 13px;
    color: #64748B;
}

/* ── Section labels ── */
#fieldLabel {
    font-size: 13px;
    font-weight: 600;
    color: #334155;
}

/* ── Input fields ── */
QLineEdit {
    height: 40px;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 0px 12px;
    font-size: 14px;
    color: #0F172A;
    background: #F8FAFC;
    selection-background-color: #2563EB;
}

QLineEdit:focus {
    border: 1.5px solid #2563EB;
    background: #FFFFFF;
    outline: none;
}

QLineEdit:hover {
    border: 1.5px solid #94A3B8;
}

/* ── Password wrapper frame ── */
#passwordFrame {
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    background: #F8FAFC;
}

#passwordFrame:focus-within {
    border: 1.5px solid #2563EB;
    background: #FFFFFF;
}

#passwordInput {
    border: none;
    border-radius: 8px;
    background: transparent;
    padding: 0px 0px 0px 12px;
}

#passwordInput:focus {
    border: none;
    background: transparent;
}

/* ── Toggle button ── */
#toggleBtn {
    border: none;
    background: transparent;
    color: #94A3B8;
    font-size: 13px;
    padding: 0px 10px;
    min-width: 36px;
}

#toggleBtn:hover {
    color: #2563EB;
}

/* ── Primary login button ── */
#loginBtn {
    height: 44px;
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

#loginBtn:hover {
    background-color: #1D4ED8;
}

#loginBtn:pressed {
    background-color: #1E40AF;
}

#loginBtn:disabled {
    background-color: #93C5FD;
}

/* ── Error label ── */
#errorLabel {
    font-size: 12px;
    color: #EF4444;
}

/* ── Divider ── */
#divider {
    color: #E2E8F0;
}
"""


# ─────────────────────────────────────────────
#  Password field with show/hide toggle
# ─────────────────────────────────────────────
class PasswordField(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("passwordFrame")
        self.setFixedHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.line_edit = QLineEdit()
        self.line_edit.setObjectName("passwordInput")
        self.line_edit.setPlaceholderText("Enter your password")
        self.line_edit.setEchoMode(QLineEdit.Password)
        self.line_edit.setFrame(False)
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.toggle_btn = QPushButton("Show")
        self.toggle_btn.setObjectName("toggleBtn")
        self.toggle_btn.setFixedWidth(46)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setFocusPolicy(Qt.NoFocus)
        self.toggle_btn.clicked.connect(self._toggle_visibility)

        layout.addWidget(self.line_edit)
        layout.addWidget(self.toggle_btn)

        self._visible = False

    def _toggle_visibility(self):
        self._visible = not self._visible
        if self._visible:
            self.line_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_btn.setText("Hide")
        else:
            self.line_edit.setEchoMode(QLineEdit.Password)
            self.toggle_btn.setText("Show")

    def text(self):
        return self.line_edit.text()

    def setPlaceholderText(self, text):
        self.line_edit.setPlaceholderText(text)


# ─────────────────────────────────────────────
#  Login Card Widget
# ─────────────────────────────────────────────
class LoginCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loginCard")
        self.setFixedWidth(420)
        self._build_ui()
        self._apply_shadow()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 40, 36, 40)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────
        title = QLabel("AU Infocity - Vendor Attendance & OT Report")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)

        subtitle = QLabel("Sign in to continue")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(subtitle)
        layout.addSpacing(32)

        # ── User ID field ────────────────────────
        user_label = QLabel("User ID / Email")
        user_label.setObjectName("fieldLabel")

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Enter your user ID or email")
        self.user_input.setFixedHeight(42)
        self.user_input.textChanged.connect(self._clear_error)

        layout.addWidget(user_label)
        layout.addSpacing(6)
        layout.addWidget(self.user_input)
        layout.addSpacing(18)

        # ── Password field ───────────────────────
        pass_label = QLabel("Password")
        pass_label.setObjectName("fieldLabel")

        self.pass_input = PasswordField()
        self.pass_input.line_edit.textChanged.connect(self._clear_error)

        layout.addWidget(pass_label)
        layout.addSpacing(6)
        layout.addWidget(self.pass_input)
        layout.addSpacing(10)

        # ── Error message ────────────────────────
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setFixedHeight(18)

        layout.addWidget(self.error_label)
        layout.addSpacing(14)

        # ── Login button ─────────────────────────
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._handle_login)

        layout.addWidget(self.login_btn)

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

    def _clear_error(self):
        self.error_label.setText("")

    def _handle_login(self):
        user_id = self.user_input.text().strip()
        password = self.pass_input.text()

        if not user_id and not password:
            self._show_error("Please enter your User ID and password.")
            self.user_input.setFocus()
            return

        if not user_id:
            self._show_error("User ID / Email is required.")
            self.user_input.setFocus()
            return

        if not password:
            self._show_error("Password is required.")
            self.pass_input.line_edit.setFocus()
            return

        # Replace this block with real auth logic
        self._on_login_success(user_id)

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self._shake()

    def _on_login_success(self, user_id: str):
        self.login_btn.setDisabled(True)
        self.login_btn.setText("Signing in…")
        # Simulate async: re-enable after a tick (replace with real logic)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._reset_button())

    def _reset_button(self):
        self.login_btn.setDisabled(False)
        self.login_btn.setText("Sign In")

    def _shake(self):
        from PyQt5.QtCore import QTimer
        origin = self.pos()
        offsets = [-8, 8, -6, 6, -4, 4, 0]

        def _step(i=0):
            if i < len(offsets):
                self.move(origin.x() + offsets[i], origin.y())
                QTimer.singleShot(40, lambda: _step(i + 1))

        _step()


# ─────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BioTime — Sign In")
        self.resize(960, 640)
        self.setMinimumSize(480, 420)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = LoginCard()
        outer.addWidget(self.card, alignment=Qt.AlignCenter)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # Smooth font rendering on macOS / Windows
    font = QFont("Inter", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
