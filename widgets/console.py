import sys
import os
import subprocess
import ast
import importlib
import tempfile
import time
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPlainTextEdit, QTextEdit, QPushButton,
    QLabel, QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog, QAction, QTabWidget,
    QToolBar, QMenuBar, QMessageBox, QFrame, QTreeWidget, QTreeWidgetItem, QInputDialog,
    QDialog, QListWidget, QLineEdit, QProgressBar, QCompleter, QCheckBox, QMenu
)
from PyQt5.QtGui import (  
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextCursor, QPainter, QTextFormat, QIcon, QTextDocument
)
from PyQt5.QtCore import QRegExp, Qt, QRect, QSize, QTimer, QProcess, QStringListModel, QFileSystemWatcher

try:
    import jedi
    JEDI_AVAILABLE = True
except ImportError:
    JEDI_AVAILABLE = False

class OutputConsole(QTextEdit):
    BACKGROUND_COLOR = "#0c0c0c"
    TEXT_COLOR = "#cccccc"
    FONT_FAMILY = "'Consolas', 'Monaco', monospace"
    FONT_SIZE_PT = 11

    def __init__(self):
        super().__init__()
        self._setup_style()
        self.setReadOnly(True)

    def _setup_style(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.BACKGROUND_COLOR};
                color: {self.TEXT_COLOR};
                border: 1px solid #3e3e3e;
                font-family: {self.FONT_FAMILY};
                font-size: {self.FONT_SIZE_PT}pt;
                padding: 5px;
            }}
        """)

    def append_line(self, text: str):
        """Konsola yeni bir satır ekler (gerektiğinde özel log formatı eklenebilir)."""
        self.append(text)

