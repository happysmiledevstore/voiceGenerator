"""
Main application window — light theme, left sidebar navigation,
stacked content pages for Voice Recorder and Text to Speech.
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QStatusBar, QScrollArea, QSpacerItem, QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor

from ui.recorder_tab import RecorderTab
from ui.tts_tab import TTSTab


def _icon_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "app_icon.ico")


# ---------------------------------------------------------------------------
# Light theme stylesheet
# ---------------------------------------------------------------------------

LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #111111;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

/* ---- Sidebar ---- */
#Sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d9d9d9;
}

#AppTitle {
    color: #111111;
    font-size: 12pt;
    font-weight: bold;
    padding: 4px 0px;
}

#NavButton {
    background-color: transparent;
    color: #333333;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 10pt;
}

#NavButton:hover {
    background-color: #eeeeee;
    color: #000000;
}

#NavButton[active="true"] {
    background-color: #e8e8e8;
    color: #000000;
    font-weight: bold;
    border-left: 3px solid #111111;
}

/* ---- Content area ---- */
#ContentArea {
    background-color: #f5f5f5;
}

/* ---- GroupBox ---- */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    color: #333333;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #111111;
}

/* ---- Standard buttons ---- */
QPushButton {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #f0f0f0;
    border-color: #888888;
    color: #000000;
}

QPushButton:pressed {
    background-color: #e0e0e0;
    border-color: #555555;
}

QPushButton:disabled {
    background-color: #f5f5f5;
    color: #aaaaaa;
    border-color: #e0e0e0;
}

/* ---- Icon tool buttons ---- */
QPushButton#IconBtn {
    background-color: #ffffff;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    padding: 6px;
    min-width: 48px;
    max-width: 48px;
    min-height: 48px;
    max-height: 48px;
}

QPushButton#IconBtn:hover {
    background-color: #eeeeee;
    border-color: #888888;
}

QPushButton#IconBtn:pressed {
    background-color: #d9d9d9;
}

QPushButton#IconBtn:disabled {
    background-color: #f5f5f5;
    border-color: #eeeeee;
}

/* Record button */
QPushButton#RecordBtn {
    background-color: #ffffff;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    padding: 6px;
    min-width: 48px;
    max-width: 48px;
    min-height: 48px;
    max-height: 48px;
}

QPushButton#RecordBtn:hover {
    background-color: #eeeeee;
    border-color: #555555;
}

QPushButton#RecordBtn[recording="true"] {
    background-color: #e8e8e8;
    border-color: #111111;
    border-width: 2px;
}

/* Generate speech button */
QPushButton#GenerateBtn {
    background-color: #111111;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 11pt;
    font-weight: bold;
}

QPushButton#GenerateBtn:hover {
    background-color: #333333;
}

QPushButton#GenerateBtn:pressed {
    background-color: #000000;
}

QPushButton#GenerateBtn:disabled {
    background-color: #bbbbbb;
    color: #ffffff;
}

/* Preset buttons */
QPushButton#PresetBtn {
    background-color: #f5f5f5;
    color: #333333;
    border: 1px solid #d9d9d9;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 9pt;
    min-height: 32px;
}

QPushButton#PresetBtn:hover {
    background-color: #e8e8e8;
    color: #000000;
    border-color: #888888;
}

QPushButton#PresetBtn:pressed {
    background-color: #d9d9d9;
}

/* Profile button */
QPushButton#ProfileBtn {
    background-color: #f5f5f5;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 6px;
    padding: 6px 14px;
}

QPushButton#ProfileBtn:hover {
    background-color: #e8e8e8;
    border-color: #888888;
    color: #000000;
}

QPushButton#ProfileBtn:disabled {
    background-color: #f5f5f5;
    color: #aaaaaa;
    border-color: #e0e0e0;
}

/* ---- Sliders ---- */
QSlider::groove:horizontal {
    height: 4px;
    background: #d9d9d9;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #111111;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    border: 2px solid #ffffff;
}

QSlider::sub-page:horizontal {
    background: #555555;
    border-radius: 2px;
}

/* ---- Combos ---- */
QComboBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 6px;
    padding: 5px 10px;
}

QComboBox::drop-down { border: none; width: 20px; }

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d9d9d9;
    selection-background-color: #e8e8e8;
    selection-color: #000000;
}

/* ---- Text edit ---- */
QTextEdit {
    background-color: #ffffff;
    color: #111111;
    border: 1px solid #cccccc;
    border-radius: 6px;
    selection-background-color: #d9d9d9;
}

/* ---- Labels ---- */
QLabel { color: #333333; }

QCheckBox { color: #333333; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #cccccc;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #111111;
    border-color: #111111;
}

QRadioButton { color: #333333; }
QRadioButton::indicator {
    width: 16px; height: 16px;
    border: 1px solid #cccccc;
    border-radius: 8px;
    background: #ffffff;
}
QRadioButton::indicator:checked {
    background: #111111;
    border-color: #111111;
}

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: #f0f0f0;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #cccccc;
    border-radius: 4px;
    min-height: 30px;
}

QStatusBar {
    background: #ffffff;
    color: #777777;
    border-top: 1px solid #d9d9d9;
    font-size: 9pt;
}
"""


# ---------------------------------------------------------------------------
# Sidebar navigation button
# ---------------------------------------------------------------------------

class NavButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("NavButton")
        self.setCheckable(False)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 10))

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Generator & Changer")
        self.setMinimumSize(900, 700)
        self.resize(1020, 780)
        self.setStyleSheet(LIGHT_STYLE)

        icon_path = _icon_path()
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root_widget = QWidget()
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root_widget)

        # ---- Sidebar -------------------------------------------------
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # ---- Content stack -------------------------------------------
        self._stack = QStackedWidget()
        self._stack.setObjectName("ContentArea")

        self._recorder_tab = RecorderTab()
        self._recorder_tab.status_message.connect(self._on_status)
        rec_scroll = self._wrap_scroll(self._recorder_tab)
        self._stack.addWidget(rec_scroll)         # index 0

        self._tts_tab = TTSTab()
        self._tts_tab.status_message.connect(self._on_status)
        tts_scroll = self._wrap_scroll(self._tts_tab)
        self._stack.addWidget(tts_scroll)         # index 1

        root_layout.addWidget(self._stack, 1)

        # ---- Status bar ----------------------------------------------
        self._statusbar = QStatusBar()
        self._statusbar.showMessage("Ready")
        self.setStatusBar(self._statusbar)

        # Activate first nav item
        self._nav_buttons[0].set_active(True)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # Logo row
        logo_row = QHBoxLayout()
        icon_path = _icon_path()
        if os.path.isfile(icon_path):
            logo_lbl = QLabel()
            pm = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pm)
            logo_row.addWidget(logo_lbl)

        title_lbl = QLabel("VoiceGen")
        title_lbl.setObjectName("AppTitle")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        logo_row.addWidget(title_lbl)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #e5e7eb; margin: 10px 0;")
        layout.addWidget(line)

        # Nav label
        nav_lbl = QLabel("NAVIGATION")
        nav_lbl.setFont(QFont("Segoe UI", 7, QFont.Bold))
        nav_lbl.setStyleSheet("color: #9ca3af; letter-spacing: 1px; padding-left: 4px;")
        layout.addWidget(nav_lbl)
        layout.addSpacing(4)

        # Nav buttons
        self._nav_buttons: list[NavButton] = []

        btn0 = NavButton("Voice Recorder")
        btn0.clicked.connect(lambda: self._switch_page(0))
        layout.addWidget(btn0)
        self._nav_buttons.append(btn0)

        btn1 = NavButton("Text to Speech")
        btn1.clicked.connect(lambda: self._switch_page(1))
        layout.addWidget(btn1)
        self._nav_buttons.append(btn1)

        layout.addStretch()

        # Version label at bottom
        ver_lbl = QLabel("v1.0.0")
        ver_lbl.setFont(QFont("Segoe UI", 8))
        ver_lbl.setStyleSheet("color: #9ca3af;")
        ver_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver_lbl)

        return sidebar

    def _switch_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)

    @staticmethod
    def _wrap_scroll(widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        return scroll

    def _on_status(self, msg: str) -> None:
        self._statusbar.showMessage(msg)
