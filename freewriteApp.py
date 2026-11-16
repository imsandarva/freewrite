import sys
from PyQt5.QtWidgets import QApplication
from app.paths import prepare_app
from app.window import FreewriteApp

if __name__ == "__main__":
    sys.argv[0] = "freewrite"
    app = QApplication(sys.argv)
    prepare_app(app)
    window = FreewriteApp()
    window.present()
    sys.exit(app.exec_())
