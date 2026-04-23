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

class Pide(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # Cache
        self.imported_modules = {}
        self.failed_modules = set()
        self.modules_name = set()

        # Color formats
        self._setup_formats()
        self._setup_highlighting_rules()

    def _setup_formats(self):
        def format_template(color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(*color))
            if bold:
                fmt.setFontWeight(QFont.Bold)
            if italic:
                fmt.setFontItalic(True)
            return fmt

        self.keyword_format            = format_template((86, 156, 214), bold=True)
        self.string_format             = format_template((206, 145, 120))
        self.comment_format            = format_template((106, 153, 85), italic=True)
        self.number_format             = format_template((181, 206, 168))
        self.function_format_success   = format_template((220, 220, 170))
        self.function_format_failure   = format_template((244, 71, 71))
        self.module_format_success     = format_template((78, 201, 176), bold=True)
        self.variable_format_decl      = format_template((255, 165, 0))
        self.variable_format_usage     = format_template((156, 120, 255))

    def _setup_highlighting_rules(self):
        self.highlighting_rules = []

        # Keywords
        keywords = [
            'def', 'class', 'if', 'elif', 'else', 'while', 'for', 'try', 'except',
            'finally', 'with', 'as', 'import', 'from', 'return', 'break', 'continue',
            'pass', 'raise', 'yield', 'lambda', 'global', 'nonlocal', 'assert',
            'del', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None'
        ]
        for word in keywords:
            pattern = QRegExp(rf'\b{word}\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

        # Built-in functions
        builtins = [
            'print', 'len', 'range', 'input', 'int', 'float', 'str', 'list', 'dict', 
            'set', 'tuple', 'open', 'close', 'sum', 'min', 'max', 'sorted', 'reversed', 
            'enumerate', 'map', 'filter', 'zip', 'abs', 'round', 'pow', 'help', 'dir', 
            'isinstance', 'issubclass', 'getattr', 'setattr', 'hasattr', 'type'
        ]
        for func in builtins:
            pattern = QRegExp(rf'\b{func}\b(?=\()')
            self.highlighting_rules.append((pattern, self.function_format_success))

        # Numbers
        self.highlighting_rules.append((QRegExp(r'\b\d+\.?\d*\b'), self.number_format))

        # Strings
        for pattern in [r'".*?"', r"'.*?'", r'""".*?"""', r"'''.*?'''"]:
            self.highlighting_rules.append((QRegExp(pattern), self.string_format))

        # Comments
        self.highlighting_rules.append((QRegExp(r'#.*'), self.comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)

        self._highlight_imports(text)
        self._highlight_variables(text)

    def _highlight_imports(self, text):
        for module_set, fmt in [
            (self.modules_name, self.module_format_success),
            (self.failed_modules, self.function_format_failure)
        ]:
            for name in module_set:
                pattern = QRegExp(rf'\b{name}\b')
                index = pattern.indexIn(text)
                while index >= 0:
                    length = pattern.matchedLength()
                    self.setFormat(index, length, fmt)
                    index = pattern.indexIn(text, index + length)

        self._highlight_module_functions(text)

    def _highlight_module_functions(self, text):
        pattern = QRegExp(r'\b(\w+)\.(\w+)\s*(?=\()')
        index = pattern.indexIn(text)

        while index >= 0:
            module_name = pattern.cap(1)
            func_name = pattern.cap(2)
            pos = pattern.pos(2)

            fmt = self.function_format_success if (
                module_name in self.imported_modules and
                hasattr(self.imported_modules[module_name], func_name)
            ) else self.function_format_failure

            self.setFormat(pos, len(func_name), fmt)
            index = pattern.indexIn(text, index + pattern.matchedLength())

    def parse_full_document(self):
        """Tüm dokümanı tek seferde parse et (her satır için değil)"""
        code = self.document().toPlainText()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._load_module(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self._load_module(node.module)
        except:
            pass

    def _load_module(self, module_name):
        if module_name in self.imported_modules or module_name in self.failed_modules:
            return
        try:
            module = importlib.import_module(module_name)
            self.imported_modules[module_name] = module
            self.modules_name.add(module_name)
        except ImportError:
            self.failed_modules.add(module_name)

    def _highlight_variables(self, text):
        pattern = QRegExp(r'\b(\w+)\s*=')
        index = pattern.indexIn(text)
        while index >= 0:
            length = len(pattern.cap(1))
            self.setFormat(index, length, self.variable_format_decl)
            index = pattern.indexIn(text, index + pattern.matchedLength())

