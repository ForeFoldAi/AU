"""Centralized QSS stylesheet for the BioTime Attendance GUI."""


def app_stylesheet() -> str:
    return _BASE + _LOGIN + _DASHBOARD


# ─────────────────────────────────────────────────────────────────────────────
#  Base / shared
# ─────────────────────────────────────────────────────────────────────────────
_BASE = """
* {
    font-size: 10pt;
}

QMainWindow,
QWidget#loginRoot,
QWidget#mainRoot,
QWidget#dashRoot {
    background-color: #F1F5F9;
}

QGroupBox {
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 10px;
    background-color: #ffffff;
    padding: 6px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    margin-left: 6px;
    color: #475569;
    font-weight: 600;
    font-size: 9pt;
}

QLabel {
    color: #1E293B;
}

QLineEdit,
QComboBox,
QSpinBox {
    background-color: #ffffff;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0F172A;
    selection-background-color: #2563EB;
    selection-color: #ffffff;
    min-height: 30px;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus {
    border: 1.5px solid #2563EB;
    background-color: #ffffff;
}

QLineEdit:hover,
QComboBox:hover,
QSpinBox:hover {
    border: 1px solid #94A3B8;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    background: #ffffff;
    selection-background-color: #EFF6FF;
    selection-color: #1D4ED8;
    padding: 4px;
}

QSpinBox::up-button,
QSpinBox::down-button {
    width: 18px;
    border: none;
    background: transparent;
}

QPushButton {
    border: 1px solid #CBD5E1;
    border-radius: 7px;
    padding: 7px 16px;
    background-color: #ffffff;
    color: #334155;
    font-weight: 600;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
}

QPushButton:pressed {
    background-color: #F1F5F9;
}

QPushButton#primaryButton {
    background-color: #2563EB;
    border-color: #2563EB;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #1D4ED8;
    border-color: #1D4ED8;
}

QPushButton#primaryButton:pressed {
    background-color: #1E40AF;
}

QPushButton#secondaryButton {
    background-color: #EFF6FF;
    border-color: #BFDBFE;
    color: #1D4ED8;
}

QPushButton#secondaryButton:hover {
    background-color: #DBEAFE;
}

QPushButton#tertiaryButton {
    background-color: #ffffff;
    color: #64748B;
}

QPushButton:disabled {
    color: #94A3B8;
    background-color: #F8FAFC;
    border-color: #E2E8F0;
}

QScrollBar:vertical {
    border: none;
    background: #F8FAFC;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #F8FAFC;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QStatusBar {
    background-color: #ffffff;
    color: #64748B;
    border-top: 1px solid #E2E8F0;
    font-size: 9pt;
}

QMessageBox {
    background-color: #ffffff;
}

QDialog {
    background-color: #F8FAFC;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

QCheckBox {
    color: #334155;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid #CBD5E1;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
}

QTextEdit#logView {
    background-color: #0F172A;
    border-radius: 8px;
    border: 1px solid #1E293B;
    color: #E2E8F0;
    padding: 8px;
    font-family: "Consolas", "Menlo", "Courier New", monospace;
    font-size: 9pt;
}
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Login screen
# ─────────────────────────────────────────────────────────────────────────────
_LOGIN = """
QWidget#loginRoot {
    background-color: #F1F5F9;
}

QFrame#loginCard {
    background-color: #ffffff;
    border-radius: 16px;
    border: none;
}

QWidget#loginRoot QLabel#titleLabel {
    color: #0F172A;
    font-size: 22px;
    font-weight: 700;
}

QWidget#loginRoot QLabel#subtitleLabel {
    color: #64748B;
    font-size: 11pt;
}

QWidget#loginRoot QLabel#fieldLabel {
    color: #334155;
    font-size: 10pt;
    font-weight: 600;
}

QWidget#loginRoot QLineEdit {
    background-color: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 0px 12px;
    height: 40px;
    color: #0F172A;
    font-size: 10pt;
}

QWidget#loginRoot QLineEdit:focus {
    border: 1.5px solid #2563EB;
    background-color: #ffffff;
}

QWidget#loginRoot QLineEdit:hover {
    border: 1.5px solid #94A3B8;
}

QFrame#passwordFrame {
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    background-color: #F8FAFC;
}

QWidget#loginRoot QLineEdit#passwordInput {
    border: none;
    background: transparent;
    padding: 0px 0px 0px 12px;
    border-radius: 0px;
}

QWidget#loginRoot QLineEdit#passwordInput:focus,
QWidget#loginRoot QLineEdit#passwordInput:hover {
    border: none;
    background: transparent;
}

QPushButton#toggleBtn {
    border: none;
    background: transparent;
    color: #94A3B8;
    font-size: 13px;
    padding: 0px 10px;
    min-width: 36px;
    min-height: 0px;
}

QPushButton#toggleBtn:hover {
    color: #2563EB;
}

QLabel#errorLabel {
    font-size: 10px;
    color: #EF4444;
}

QPushButton#loginButton {
    background-color: #2563EB;
    border: none;
    color: #ffffff;
    border-radius: 8px;
    padding: 10px;
    font-size: 10pt;
    font-weight: 700;
    min-height: 44px;
}

QPushButton#loginButton:hover {
    background-color: #1D4ED8;
}

QPushButton#loginButton:pressed {
    background-color: #1E40AF;
}

QPushButton#loginButton:disabled {
    background-color: #93C5FD;
}
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────────────────────
_DASHBOARD = """
/* ── Header bar ── */
QWidget#headerBar {
    background-color: #ffffff;
    border-bottom: 1px solid #E2E8F0;
}

QLabel#appName {
    font-size: 15px;
    font-weight: 700;
    color: #0F172A;
}

QLabel#userInfo {
    font-size: 10pt;
    color: #64748B;
}

QPushButton#logoutBtn {
    background-color: #FEF2F2;
    border: 1px solid #FECACA;
    color: #DC2626;
    border-radius: 7px;
    padding: 6px 14px;
    font-weight: 600;
    min-height: 0px;
}

QPushButton#logoutBtn:hover {
    background-color: #FEE2E2;
}

/* ── Tab bar ── */
QTabWidget#dashTabs::pane {
    border: none;
    background-color: #F1F5F9;
}

QTabWidget#dashTabs QTabBar {
    background-color: #ffffff;
}

QTabWidget#dashTabs QTabBar::tab {
    background-color: #ffffff;
    color: #64748B;
    font-weight: 500;
    font-size: 10pt;
    padding: 12px 24px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabWidget#dashTabs QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2563EB;
    border-bottom: 2px solid #2563EB;
    font-weight: 600;
}

QTabWidget#dashTabs QTabBar::tab:hover:!selected {
    background-color: #F8FAFC;
    color: #334155;
}

/* ── Stat card ── */
QFrame#statCard {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

QLabel#statValue {
    font-size: 28px;
    font-weight: 700;
    color: #0F172A;
}

QLabel#statLabel {
    font-size: 9pt;
    color: #64748B;
    font-weight: 500;
}

/* ── Employee table ── */
QTableView#employeeTable {
    background-color: #ffffff;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: #F1F5F9;
    selection-background-color: #EFF6FF;
    selection-color: #1E293B;
    alternate-background-color: #F8FAFC;
    color: #1E293B;
}

QTableView#employeeTable::item {
    padding: 8px 12px;
    border: none;
    color: #1E293B;
    background-color: transparent;
}

QTableView#employeeTable::item:alternate {
    background-color: #F8FAFC;
    color: #1E293B;
}

QTableView#employeeTable::item:selected {
    background-color: #EFF6FF;
    color: #1E293B;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: 600;
    font-size: 9pt;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    border-right: 1px solid #F1F5F9;
}

QHeaderView::section:last {
    border-right: none;
}

/* ── Search / filter bar ── */
QLineEdit#searchInput {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 6px 12px 6px 34px;
    background: #ffffff;
    font-size: 10pt;
    color: #334155;
    min-height: 34px;
}

QLineEdit#searchInput:focus {
    border: 1.5px solid #2563EB;
}

QComboBox#filterCombo {
    min-height: 34px;
    padding: 4px 10px;
    border-radius: 8px;
}

/* ── Status badge ── */
QLabel#badgeActive {
    background-color: #DCFCE7;
    color: #15803D;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: 600;
    font-size: 9pt;
}

QLabel#badgeInactive {
    background-color: #FEE2E2;
    color: #DC2626;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: 600;
    font-size: 9pt;
}

/* ── Report cards ── */
QFrame#reportCard {
    background-color: #ffffff;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

QFrame#reportCard:hover {
    border-color: #BFDBFE;
    background-color: #FAFCFF;
}

QLabel#reportCardTitle {
    font-size: 12pt;
    font-weight: 700;
    color: #0F172A;
}

QLabel#reportCardDesc {
    font-size: 9pt;
    color: #64748B;
}

QLabel#reportCardIcon {
    font-size: 28px;
}

/* ── Section titles inside tabs ── */
QLabel#sectionTitle {
    font-size: 14pt;
    font-weight: 700;
    color: #0F172A;
}

QLabel#sectionSubtitle {
    font-size: 10pt;
    color: #64748B;
}
"""
