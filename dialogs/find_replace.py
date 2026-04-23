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

class FindReplaceDialog(QDialog):
    """Find & Replace dialog"""
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Find & Replace")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Find section
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Search text...")
        self.find_input.textChanged.connect(self._on_find_text_changed)
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)
        
        # Replace section
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replacement text...")
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("Case sensitive")
        self.whole_word_cb = QCheckBox("Whole word")
        self.regex_cb = QCheckBox("Regex")
        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.whole_word_cb)
        options_layout.addWidget(self.regex_cb)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        find_next_btn = QPushButton("⬇ Find Next")
        find_next_btn.clicked.connect(self._find_next)
        find_next_btn.setShortcut("F3")
        btn_layout.addWidget(find_next_btn)
        
        find_prev_btn = QPushButton("⬆ Find Previous")
        find_prev_btn.clicked.connect(self._find_previous)
        find_prev_btn.setShortcut("Shift+F3")
        btn_layout.addWidget(find_prev_btn)
        
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self._replace)
        btn_layout.addWidget(replace_btn)
        
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self._replace_all)
        btn_layout.addWidget(replace_all_btn)
        
        layout.addLayout(btn_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4caf50; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                padding: 5px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #404040;
                color: #d4d4d4;
                border: 1px solid #555555;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QCheckBox {
                color: #d4d4d4;
            }
        """)
        
        self.find_input.setFocus()
    
    def _get_search_flags(self):
        """QTextDocument search flags'lerini al"""
        flags = QTextDocument.FindFlags()
        if self.case_sensitive_cb.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_word_cb.isChecked():
            flags |= QTextDocument.FindWholeWords
        return flags
    
    def _on_find_text_changed(self):
        """Find text değiştiğinde ilk eşleşmeyi bul"""
        if self.find_input.text():
            self._find_next()
    
    def _find_next(self):
        """Sonraki eşleşmeyi bul"""
        search_text = self.find_input.text()
        if not search_text:
            return
        
        cursor = self.editor.textCursor()
        
        if self.regex_cb.isChecked():
            # Regex search
            pattern = QRegExp(search_text)
            if not self.case_sensitive_cb.isChecked():
                pattern.setCaseSensitivity(Qt.CaseInsensitive)
            found_cursor = self.editor.document().find(pattern, cursor)
        else:
            # Normal search
            found_cursor = self.editor.document().find(search_text, cursor, self._get_search_flags())
        
        if not found_cursor.isNull():
            self.editor.setTextCursor(found_cursor)
            self.status_label.setText("✓ Found")
            self.status_label.setStyleSheet("color: #4caf50;")
        else:
            # Başa dön
            cursor.movePosition(QTextCursor.Start)
            self.editor.setTextCursor(cursor)
            self.status_label.setText("⚠ Not found (wrapped to start)")
            self.status_label.setStyleSheet("color: #ff9800;")
    
    def _find_previous(self):
        """Önceki eşleşmeyi bul"""
        search_text = self.find_input.text()
        if not search_text:
            return
        
        cursor = self.editor.textCursor()
        flags = self._get_search_flags() | QTextDocument.FindBackward
        
        if self.regex_cb.isChecked():
            pattern = QRegExp(search_text)
            if not self.case_sensitive_cb.isChecked():
                pattern.setCaseSensitivity(Qt.CaseInsensitive)
            found_cursor = self.editor.document().find(pattern, cursor, QTextDocument.FindBackward)
        else:
            found_cursor = self.editor.document().find(search_text, cursor, flags)
        
        if not found_cursor.isNull():
            self.editor.setTextCursor(found_cursor)
            self.status_label.setText("✓ Found")
            self.status_label.setStyleSheet("color: #4caf50;")
        else:
            # Sona git
            cursor.movePosition(QTextCursor.End)
            self.editor.setTextCursor(cursor)
            self.status_label.setText("⚠ Not found (wrapped to end)")
            self.status_label.setStyleSheet("color: #ff9800;")
    
    def _replace(self):
        """Mevcut eşleşmeyi değiştir"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
            self.status_label.setText("✓ Replaced")
            self.status_label.setStyleSheet("color: #4caf50;")
            self._find_next()
    
    def _replace_all(self):
        """Tüm eşleşmeleri değiştir"""
        search_text = self.find_input.text()
        replace_text = self.replace_input.text()
        
        if not search_text:
            return
        
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        # Başa git
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)
        
        count = 0
        while True:
            if self.regex_cb.isChecked():
                pattern = QRegExp(search_text)
                if not self.case_sensitive_cb.isChecked():
                    pattern.setCaseSensitivity(Qt.CaseInsensitive)
                found_cursor = self.editor.document().find(pattern, cursor)
            else:
                found_cursor = self.editor.document().find(search_text, cursor, self._get_search_flags())
            
            if found_cursor.isNull():
                break
            
            found_cursor.insertText(replace_text)
            cursor = found_cursor
            count += 1
        
        cursor.endEditBlock()
        self.status_label.setText(f"✓ Replaced {count} occurrence(s)")
        self.status_label.setStyleSheet("color: #4caf50;")

