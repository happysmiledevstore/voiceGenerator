"""
Voice Generator & Changer — entry point.

Usage:
    python main.py

Requirements:
    pip install -r requirements.txt
"""

import os
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from ui.main_window import MainWindow, _icon_path


def handle_exception(exc_type, exc_value, exc_tb):
    """Global uncaught exception handler — shows a dialog instead of crashing silently."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[UNHANDLED EXCEPTION]\n{msg}", file=sys.stderr)
    try:
        dlg = QMessageBox()
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Unexpected Error")
        dlg.setText("An unexpected error occurred.")
        dlg.setDetailedText(msg)
        dlg.exec_()
    except Exception:
        pass


def main() -> None:
    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Voice Generator & Changer")
    app.setApplicationVersion("1.0.0")
    app.setFont(QFont("Segoe UI", 10))

    icon_path = _icon_path()
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    sys.excepthook = handle_exception

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
