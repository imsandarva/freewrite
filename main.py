import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QLocale
from app.paths import prepare_app
from app.window import FreewriteApp


def main():
    # The process name is what the desktop uses to match this window to its icon.
    sys.argv[0] = "freewrite"
    app = QApplication(sys.argv)
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    prepare_app(app)
    window = FreewriteApp()
    window.present()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
