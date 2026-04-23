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

class TerminalWidget(QWidget):
    """Embedded terminal widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #0c0c0c;
                color: #00ff00;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11pt;
                padding: 5px;
            }
        """)
        layout.addWidget(self.output)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_label = QLabel("$")
        self.input_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        self.input_field = QPlainTextEdit()
        self.input_field.setMaximumHeight(30)
        self.input_field.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11pt;
                padding: 2px;
            }
        """)
        self.input_field.installEventFilter(self)
        
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_field)
        layout.addLayout(input_layout)
        
        # Process setup
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._process_finished)
        
        self._start_shell()
        
    def _start_shell(self):
        """Terminal shell başlat"""
        if sys.platform == "win32":
            self.process.start("cmd.exe")
        else:
            self.process.start("/bin/bash")
        self.output.append("<b style='color:#4caf50'>Terminal başlatıldı. Komut girin...</b>\n")
    
    def _handle_stdout(self):
        """Standart çıktıyı işle"""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.output.insertPlainText(data)
        self.output.moveCursor(QTextCursor.End)
    
    def _handle_stderr(self):
        """Hata çıktısını işle"""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.output.insertHtml(f"<span style='color:#f44336'>{data}</span>")
        self.output.moveCursor(QTextCursor.End)
    
    def _process_finished(self):
        """Process bittiğinde"""
        self.output.append("\n<b style='color:#ff9800'>Terminal kapatıldı.</b>")
    
    def eventFilter(self, obj, event):
        """Enter tuşunu yakala"""
        if obj == self.input_field and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers():
                self._execute_command()
                return True
        return super().eventFilter(obj, event)
    
    def _execute_command(self):
        """Komutu çalıştır"""
        command = self.input_field.toPlainText().strip()
        if command:
            self.output.append(f"<b style='color:#00ff00'>$ {command}</b>")
            self.process.write(f"{command}\n".encode())
            self.input_field.clear()
    
    def clear_output(self):
        """Terminal çıktısını temizle"""
        self.output.clear()

