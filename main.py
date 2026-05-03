import sys
from PyQt5.QtWidgets import QApplication

from ui.main_window import ModernPythonIDE

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ide = ModernPythonIDE()
    ide.show()
    sys.exit(app.exec_())
