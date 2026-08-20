"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from gelotech_ai.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GeloTech AI")
    app.setOrganizationName("GeloTech")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
