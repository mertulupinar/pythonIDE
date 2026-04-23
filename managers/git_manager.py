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

class GitManagerDialog(QDialog):
    """Git yöneticisi GUI"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Git Yöneticisi")
        self.setMinimumSize(700, 600)
        self.repo_path = os.getcwd()
        
        layout = QVBoxLayout(self)
        
        # Repo path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Repo:"))
        self.path_label = QLabel(self.repo_path)
        self.path_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        path_layout.addWidget(self.path_label)
        path_layout.addStretch()
        layout.addLayout(path_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        status_btn = QPushButton("📊 Status")
        status_btn.clicked.connect(self._git_status)
        btn_layout.addWidget(status_btn)
        
        add_btn = QPushButton("➕ Add All")
        add_btn.clicked.connect(self._git_add_all)
        btn_layout.addWidget(add_btn)
        
        commit_btn = QPushButton("💾 Commit")
        commit_btn.clicked.connect(self._git_commit)
        btn_layout.addWidget(commit_btn)
        
        push_btn = QPushButton("⬆ Push")
        push_btn.clicked.connect(self._git_push)
        push_btn.setStyleSheet("background-color: #16825d; color: white;")
        btn_layout.addWidget(push_btn)
        
        pull_btn = QPushButton("⬇ Pull")
        pull_btn.clicked.connect(self._git_pull)
        pull_btn.setStyleSheet("background-color: #1976d2; color: white;")
        btn_layout.addWidget(pull_btn)
        
        layout.addLayout(btn_layout)
        
        # Commit message
        layout.addWidget(QLabel("Commit Mesajı:"))
        self.commit_input = QTextEdit()
        self.commit_input.setMaximumHeight(80)
        self.commit_input.setPlaceholderText("Commit mesajını buraya yazın...")
        self.commit_input.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', monospace;
            }
        """)
        layout.addWidget(self.commit_input)
        
        # Output
        layout.addWidget(QLabel("Output:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #0c0c0c;
                color: #cccccc;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.output)
        
        self._git_status()  # İlk açılışta status göster
    
    def _run_git_command(self, command):
        """Git komutunu çalıştır"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
                shell=True if sys.platform == "win32" else False
            )
            
            output = result.stdout + result.stderr
            return result.returncode, output
            
        except Exception as e:
            return -1, f"Hata: {str(e)}"
    
    def _git_status(self):
        """Git status göster"""
        self.output.append("<b style='color:#4caf50'>$ git status</b>")
        returncode, output = self._run_git_command(["git", "status"])
        
        if returncode == 0:
            self.output.append(output)
        else:
            self.output.append(f"<span style='color:#f44336'>{output}</span>")
    
    def _git_add_all(self):
        """Tüm değişiklikleri stage'e ekle"""
        self.output.append("<b style='color:#4caf50'>$ git add .</b>")
        returncode, output = self._run_git_command(["git", "add", "."])
        
        if returncode == 0:
            self.output.append("<span style='color:#4caf50'>✓ Tüm dosyalar stage'e eklendi</span>")
            self._git_status()
        else:
            self.output.append(f"<span style='color:#f44336'>{output}</span>")
    
    def _git_commit(self):
        """Commit yap"""
        message = self.commit_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Uyarı", "Commit mesajı giriniz!")
            return
        
        self.output.append(f"<b style='color:#4caf50'>$ git commit -m \"{message}\"</b>")
        returncode, output = self._run_git_command(["git", "commit", "-m", message])
        
        if returncode == 0:
            self.output.append(f"<span style='color:#4caf50'>✓ Commit başarılı!\n{output}</span>")
            self.commit_input.clear()
            self._git_status()
        else:
            self.output.append(f"<span style='color:#f44336'>{output}</span>")
    
    def _git_push(self):
        """Push yap"""
        reply = QMessageBox.question(
            self, "Onay",
            "Değişiklikleri remote repository'ye push etmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.output.append("<b style='color:#4caf50'>$ git push</b>")
        returncode, output = self._run_git_command(["git", "push"])
        
        if returncode == 0:
            self.output.append(f"<span style='color:#4caf50'>✓ Push başarılı!\n{output}</span>")
        else:
            self.output.append(f"<span style='color:#f44336'>{output}</span>")
    
    def _git_pull(self):
        """Pull yap"""
        self.output.append("<b style='color:#4caf50'>$ git pull</b>")
        returncode, output = self._run_git_command(["git", "pull"])
        
        if returncode == 0:
            self.output.append(f"<span style='color:#4caf50'>✓ Pull başarılı!\n{output}</span>")
            self._git_status()
        else:
            self.output.append(f"<span style='color:#f44336'>{output}</span>")

