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

class LineNumberArea(QWidget):
    BACKGROUND_COLOR = QColor(45, 45, 45)
    TEXT_COLOR = QColor(133, 133, 133)
    BORDER_COLOR = QColor(62, 62, 62)
    PADDING = 5

    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.BACKGROUND_COLOR.name()};
                color: {self.TEXT_COLOR.name()};
                border-right: 1px solid {self.BORDER_COLOR.name()};
            }}
        """)

    def sizeHint(self):
        """ Satır numara alanının ideal genişliği. """
        width = self.code_editor.line_number_area_width()
        return QSize(width, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.BACKGROUND_COLOR)

        block = self.code_editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.code_editor.blockBoundingGeometry(block).translated(self.code_editor.contentOffset()).top()
        bottom = top + self.code_editor.blockBoundingRect(block).height()
        font_height = self.code_editor.fontMetrics().height()
        line_width = self.width() - self.PADDING

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_number = str(block_number + 1)
                painter.setPen(self.TEXT_COLOR)
                painter.drawText(0, int(top), line_width, font_height, Qt.AlignRight, line_number)

            block = block.next()
            top = bottom
            bottom = top + self.code_editor.blockBoundingRect(block).height()
            block_number += 1


class Minimap(QWidget):
    """Code overview minimap"""
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
        self.setFixedWidth(120)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-left: 1px solid #3e3e3e;
            }
        """)
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(26, 26, 26))
        
        doc = self.code_editor.document()
        total_lines = doc.blockCount()
        
        if total_lines == 0:
            return
        
        # Minimap boyutları
        map_height = self.height()
        map_width = self.width()
        line_height = max(1, map_height / total_lines)
        
        # Font ayarları
        font = QFont('Consolas', 2)
        painter.setFont(font)
        
        # Her satırı çiz
        block = doc.begin()
        line_num = 0
        
        while block.isValid():
            y = int(line_num * line_height)
            text = block.text()
            
            if text.strip():
                # Kod satırı - daha parlak
                painter.setPen(QColor(100, 100, 100))
                painter.drawLine(0, y, map_width, y)
                
                # Satır uzunluğuna göre çizgi uzunluğu
                rel_length = min(len(text) / 100.0, 1.0)
                painter.setPen(QColor(180, 180, 180))
                painter.drawLine(0, y, int(map_width * rel_length), y)
            
            block = block.next()
            line_num += 1
        
        # Visible area göstergesi
        first_visible = self.code_editor.firstVisibleBlock().blockNumber()
        visible_lines = self.code_editor.viewport().height() / self.code_editor.fontMetrics().height()
        last_visible = min(first_visible + int(visible_lines), total_lines)
        
        visible_start_y = int(first_visible * line_height)
        visible_height = int((last_visible - first_visible) * line_height)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 122, 204, 60))
        painter.drawRect(0, visible_start_y, map_width, visible_height)
        
        painter.setPen(QColor(0, 122, 204))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, visible_start_y, map_width - 1, visible_height)
    
    def mousePressEvent(self, event):
        """Minimap'e tıklanınca o satıra git"""
        doc = self.code_editor.document()
        total_lines = doc.blockCount()
        
        click_y = event.y()
        map_height = self.height()
        
        line_num = int((click_y / map_height) * total_lines)
        line_num = max(0, min(line_num, total_lines - 1))
        
        # O satıra scroll et
        cursor = QTextCursor(doc.findBlockByLineNumber(line_num))
        self.code_editor.setTextCursor(cursor)
        self.code_editor.centerCursor()
    
    def wheelEvent(self, event):
        """Mouse wheel ile scroll"""
        self.code_editor.wheelEvent(event)


class ModernCodeEditor(QPlainTextEdit):
    INDENT_SIZE = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.minimap = Minimap(self)
        self.error_lines = []  # Hata satırlarını sakla

        self._setup_appearance()
        self._setup_autocomplete()
        self._connect_signals()
        self._init_state()

    def _setup_appearance(self):
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12pt;
                line-height: 1.4;
                selection-background-color: #264f78;
            }
        """)
        font = QFont('Consolas', 12)
        font.setFixedPitch(True)
        self.setFont(font)
        self.highlighter = Pide(self.document())
    
    def _setup_autocomplete(self):
        """Autocomplete (Ctrl+Space) için QCompleter kur"""
        # Snippet şablonları
        self.snippets = {
            'def': 'def function_name():\n    pass',
            'class': 'class ClassName:\n    def __init__(self):\n        pass',
            'if': 'if condition:\n    pass',
            'for': 'for item in items:\n    pass',
            'while': 'while condition:\n    pass',
            'try': 'try:\n    pass\nexcept Exception as e:\n    pass',
            'with': 'with open("file.txt", "r") as f:\n    content = f.read()',
            'main': 'if __name__ == "__main__":\n    pass',
            'init': 'def __init__(self):\n    pass',
            'str': 'def __str__(self):\n    return ""',
            'repr': 'def __repr__(self):\n    return ""',
        }
        
        # Python keywords ve builtins
        keywords = [
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
            'try', 'while', 'with', 'yield'
        ]
        
        builtins = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
            'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter',
            'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
            'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
            'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
            'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
            'super', 'tuple', 'type', 'vars', 'zip', '__import__'
        ]
        
        # Common modules
        modules = [
            'os', 'sys', 'math', 'random', 'datetime', 'time', 'json', 're',
            'collections', 'itertools', 'functools', 'pathlib', 'subprocess',
            'threading', 'multiprocessing', 'requests', 'numpy', 'pandas'
        ]
        
        # Tüm kelimeler
        self.autocomplete_words = sorted(set(keywords + builtins + modules))
        
        # QCompleter oluştur
        self.completer = QCompleter(self.autocomplete_words)
        self.completer.setWidget(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.activated.connect(self._insert_completion)
        
        # Completer popup stili
        self.completer.popup().setStyleSheet("""
            QListView {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #007acc;
                selection-background-color: #094771;
                font-family: 'Consolas', monospace;
                font-size: 11pt;
            }
        """)
    
    def _insert_completion(self, completion):
        """Seçilen completion'ı ekle"""
        cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        cursor.movePosition(QTextCursor.Left)
        cursor.movePosition(QTextCursor.EndOfWord)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)
    
    def _text_under_cursor(self):
        """Cursor altındaki kelimeyi al"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()

    def _connect_signals(self):
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.updateRequest.connect(lambda: self.minimap.update())  # Minimap güncelle
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self._on_text_changed)
        self.textChanged.connect(lambda: self.minimap.update())  # Minimap güncelle
        
    def _on_text_changed(self):
        """Metin değiştiğinde module'leri yeniden parse et"""
        if hasattr(self, '_parse_timer'):
            self._parse_timer.stop()
        else:
            self._parse_timer = QTimer()
            self._parse_timer.setSingleShot(True)
            self._parse_timer.timeout.connect(lambda: self.highlighter.parse_full_document())
        self._parse_timer.start(1000)  # 1 saniye bekle

    def _init_state(self):
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        
        # Line number area (sol)
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        
        # Minimap (sağ)
        minimap_width = self.minimap.width()
        self.minimap.setGeometry(QRect(cr.right() - minimap_width, cr.top(), minimap_width, cr.height()))

    def line_number_area_paint_event(self, event):
        self.line_number_area.paintEvent(event)

    def highlight_current_line(self):
        if self.isReadOnly():
            return

        extra_selections = []
        
        # Hata satırlarını vurgula (kırmızı)
        for line_num in self.error_lines:
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(255, 0, 0, 40))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = QTextCursor(self.document().findBlockByLineNumber(line_num - 1))
            selection.cursor = cursor
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        # Mevcut satırı vurgula (gri)
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(46, 46, 46, 100))
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extra_selections.append(selection)

        self.setExtraSelections(extra_selections)
    
    def set_error_lines(self, line_numbers):
        """Hata satırlarını ayarla ve vurgula"""
        self.error_lines = line_numbers
        self.highlight_current_line()
        
    def clear_error_lines(self):
        """Hata vurgularını temizle"""
        self.error_lines = []
        self.highlight_current_line()

    def keyPressEvent(self, event):
        # Ctrl+Space: Autocomplete
        if event.key() == Qt.Key_Space and event.modifiers() == Qt.ControlModifier:
            self._show_autocomplete()
            return
        
        # Completer açıksa ve özel tuşlar
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
        
        cursor = self.textCursor()
        key = event.key()

        auto_pairs = {
            Qt.Key_ParenLeft: '()',
            Qt.Key_BraceLeft: '{}',
            Qt.Key_BracketLeft: '[]',
            Qt.Key_QuoteDbl: '""',
            Qt.Key_Apostrophe: "''",
        }

        if key == Qt.Key_Tab:
            # Snippet expansion kontrolü
            if self._try_expand_snippet():
                return
            # Normal tab
            self.insertPlainText(" " * self.INDENT_SIZE)

        elif key == Qt.Key_Return:
            current_line = cursor.block().text()
            leading_spaces = len(current_line) - len(current_line.lstrip(' '))
            if current_line.strip().endswith(':'):
                leading_spaces += self.INDENT_SIZE
            super().keyPressEvent(event)
            self.insertPlainText(" " * leading_spaces)

        elif key in auto_pairs:
            pair = auto_pairs[key]
            self.insertPlainText(pair)
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)

        else:
            super().keyPressEvent(event)
            
        # Her tuşa basıldığında autocomplete güncelle (sadece harf/rakam ise)
        if event.text().isalnum() or event.text() == '_':
            self._update_autocomplete()
    
    def _show_autocomplete(self):
        """Autocomplete popup'ı göster"""
        completion_prefix = self._text_under_cursor()
        if len(completion_prefix) < 1:
            return
        
        self.completer.setCompletionPrefix(completion_prefix)
        popup = self.completer.popup()
        popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
        
        cursor_rect = self.cursorRect()
        cursor_rect.setWidth(
            self.completer.popup().sizeHintForColumn(0) + 
            self.completer.popup().verticalScrollBar().sizeHint().width()
        )
        self.completer.complete(cursor_rect)
    
    def _update_autocomplete(self):
        """Yazarken autocomplete'i otomatik güncelle"""
        completion_prefix = self._text_under_cursor()
        if len(completion_prefix) < 2:  # En az 2 karakter
            self.completer.popup().hide()
            return
        
        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
    
    def _try_expand_snippet(self):
        """Tab tuşuna basıldığında snippet expand et"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText().strip()
        
        if word in self.snippets:
            # Snippet'i expand et
            snippet = self.snippets[word]
            cursor.insertText(snippet)
            
            # Cursor'u ilk düzenlenebilir yere taşı (ilk kelime)
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(snippet))
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
            
            return True
        return False


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


class PipManagerDialog(QDialog):
    """Pip paket yöneticisi GUI"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paket Yöneticisi (pip)")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Üst kontroller
        top_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Paket ara (PyPI)...")
        self.search_input.textChanged.connect(self._filter_packages)
        top_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._load_installed_packages)
        top_layout.addWidget(refresh_btn)
        
        layout.addLayout(top_layout)
        
        # Paket listesi
        self.package_list = QListWidget()
        self.package_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        layout.addWidget(self.package_list)
        
        # Alt kontroller
        bottom_layout = QHBoxLayout()
        
        self.install_input = QLineEdit()
        self.install_input.setPlaceholderText("Kurulacak paket adı (örn: requests)")
        bottom_layout.addWidget(self.install_input)
        
        install_btn = QPushButton("📦 Kur")
        install_btn.clicked.connect(self._install_package)
        install_btn.setStyleSheet("background-color: #16825d; color: white; font-weight: bold;")
        bottom_layout.addWidget(install_btn)
        
        uninstall_btn = QPushButton("🗑 Kaldır")
        uninstall_btn.clicked.connect(self._uninstall_package)
        uninstall_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")
        bottom_layout.addWidget(uninstall_btn)
        
        layout.addLayout(bottom_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log area
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        self.log.setStyleSheet("""
            QTextEdit {
                background-color: #0c0c0c;
                color: #cccccc;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.log)
        
        self._load_installed_packages()
    
    def _load_installed_packages(self):
        """Yüklü paketleri listele"""
        self.log.append("<b>Paketler yükleniyor...</b>")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=columns"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.package_list.clear()
            lines = result.stdout.strip().split('\n')[2:]  # İlk 2 satır başlık
            
            for line in lines:
                if line.strip():
                    self.package_list.addItem(line)
            
            self.log.append(f"<span style='color:#4caf50'>✓ {len(lines)} paket listelendi.</span>")
            
        except Exception as e:
            self.log.append(f"<span style='color:#f44336'>Hata: {str(e)}</span>")
        finally:
            self.progress_bar.setVisible(False)
    
    def _filter_packages(self, text):
        """Paket listesini filtrele"""
        for i in range(self.package_list.count()):
            item = self.package_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def _install_package(self):
        """Paket kur"""
        package = self.install_input.text().strip()
        if not package:
            QMessageBox.warning(self, "Uyarı", "Paket adı giriniz!")
            return
        
        self.log.append(f"<b>'{package}' paketi kuruluyor...</b>")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log.append(f"<span style='color:#4caf50'>✓ '{package}' başarıyla kuruldu!</span>")
                self.install_input.clear()
                self._load_installed_packages()
            else:
                self.log.append(f"<span style='color:#f44336'>Hata:\n{result.stderr}</span>")
                
        except Exception as e:
            self.log.append(f"<span style='color:#f44336'>Hata: {str(e)}</span>")
        finally:
            self.progress_bar.setVisible(False)
    
    def _uninstall_package(self):
        """Seçili paketi kaldır"""
        selected = self.package_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Kaldırılacak paketi seçiniz!")
            return
        
        package_line = selected.text()
        package_name = package_line.split()[0]  # İlk kelime paket adı
        
        reply = QMessageBox.question(
            self, "Onay",
            f"'{package_name}' paketini kaldırmak istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.log.append(f"<b>'{package_name}' paketi kaldırılıyor...</b>")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", package_name, "-y"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log.append(f"<span style='color:#4caf50'>✓ '{package_name}' başarıyla kaldırıldı!</span>")
                self._load_installed_packages()
            else:
                self.log.append(f"<span style='color:#f44336'>Hata:\n{result.stderr}</span>")
                
        except Exception as e:
            self.log.append(f"<span style='color:#f44336'>Hata: {str(e)}</span>")
        finally:
            self.progress_bar.setVisible(False)


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


class ModernPythonIDE(QMainWindow):
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    LEFT_PANEL_WIDTH = 250
    CONSOLE_HEIGHT = 200

    def __init__(self):
        super().__init__()

        # Dinamik base path
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Taşınabilir ikon yolları
        self.ICON_FOLDER = os.path.join(self.BASE_DIR, "icons", "folder.png")
        self.ICON_PYTHON = os.path.join(self.BASE_DIR, "icons", "python.png")
        self.ICON_FILE   = os.path.join(self.BASE_DIR, "icons", "file.png")

        # Pencere ayarları
        self.tab_file_paths = {}  # Her tab için dosya yolunu sakla
        self.setWindowTitle("PyIDE - Professional Python Development Environment")
        self.setGeometry(100, 100, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        # UI kur
        self._apply_theme()
        self._init_main_layout()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()


    def _apply_theme(self, theme='default'):
        """Tema uygula - 7 farklı tema"""
        if theme == "dracula":
            self.setStyleSheet("""
                QMainWindow { background-color: #282a36; color: #f8f8f2; }
                QMenuBar { background-color: #44475a; color: #f8f8f2; }
                QMenuBar::item:selected { background-color: #6272a4; }
                QToolBar { background-color: #44475a; spacing: 5px; }
                QPushButton {
                    background-color: #6272a4;
                    color: #f8f8f2;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #7081b9; }
                QSplitter::handle { background-color: #44475a; }
                QTabWidget::pane { border: 1px solid #44475a; background-color: #282a36; }
                QTabBar::tab {
                    background-color: #44475a;
                    color: #f8f8f2;
                    padding: 8px 16px;
                    border: 1px solid #44475a;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #282a36;
                    border-bottom: 2px solid #bd93f9;
                }
                QStatusBar {
                    background-color: #bd93f9;
                    color: black;
                    border-top: 1px solid #44475a;
                }
            """)
        elif theme == "nord":
            self.setStyleSheet("""
                QMainWindow { background-color: #2e3440; color: #d8dee9; }
                QMenuBar { background-color: #3b4252; color: #d8dee9; }
                QMenuBar::item:selected { background-color: #4c566a; }
                QToolBar { background-color: #3b4252; spacing: 5px; }
                QPushButton {
                    background-color: #5e81ac;
                    color: #eceff4;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #81a1c1; }
                QSplitter::handle { background-color: #4c566a; }
                QTabWidget::pane { border: 1px solid #4c566a; background-color: #2e3440; }
                QTabBar::tab {
                    background-color: #3b4252;
                    color: #d8dee9;
                    padding: 8px 16px;
                    border: 1px solid #4c566a;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #2e3440;
                    border-bottom: 2px solid #88c0d0;
                }
                QStatusBar {
                    background-color: #88c0d0;
                    color: black;
                    border-top: 1px solid #4c566a;
                }
            """)
        elif theme == "monokai":
            self.setStyleSheet("""
                QMainWindow { background-color: #272822; color: #f8f8f2; }
                QMenuBar { background-color: #3e3d32; color: #f8f8f2; }
                QMenuBar::item:selected { background-color: #49483e; }
                QToolBar { background-color: #3e3d32; spacing: 5px; }
                QPushButton {
                    background-color: #66d9ef;
                    color: #272822;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #a1efe4; }
                QSplitter::handle { background-color: #49483e; }
                QTabWidget::pane { border: 1px solid #49483e; background-color: #272822; }
                QTabBar::tab {
                    background-color: #3e3d32;
                    color: #f8f8f2;
                    padding: 8px 16px;
                    border: 1px solid #49483e;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #272822;
                    border-bottom: 2px solid #a6e22e;
                }
                QStatusBar {
                    background-color: #a6e22e;
                    color: #272822;
                    border-top: 1px solid #49483e;
                }
            """)
        elif theme == "solarized_dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #002b36; color: #839496; }
                QMenuBar { background-color: #073642; color: #839496; }
                QMenuBar::item:selected { background-color: #586e75; }
                QToolBar { background-color: #073642; spacing: 5px; }
                QPushButton {
                    background-color: #268bd2;
                    color: #fdf6e3;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2aa198; }
                QSplitter::handle { background-color: #586e75; }
                QTabWidget::pane { border: 1px solid #586e75; background-color: #002b36; }
                QTabBar::tab {
                    background-color: #073642;
                    color: #839496;
                    padding: 8px 16px;
                    border: 1px solid #586e75;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #002b36;
                    border-bottom: 2px solid #b58900;
                }
                QStatusBar {
                    background-color: #b58900;
                    color: #002b36;
                    border-top: 1px solid #586e75;
                }
            """)
        elif theme == "one_dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #282c34; color: #abb2bf; }
                QMenuBar { background-color: #21252b; color: #abb2bf; }
                QMenuBar::item:selected { background-color: #2c313c; }
                QToolBar { background-color: #21252b; spacing: 5px; }
                QPushButton {
                    background-color: #61afef;
                    color: #282c34;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #84c0f6; }
                QSplitter::handle { background-color: #2c313c; }
                QTabWidget::pane { border: 1px solid #2c313c; background-color: #282c34; }
                QTabBar::tab {
                    background-color: #21252b;
                    color: #abb2bf;
                    padding: 8px 16px;
                    border: 1px solid #2c313c;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #282c34;
                    border-bottom: 2px solid #98c379;
                }
                QStatusBar {
                    background-color: #98c379;
                    color: #282c34;
                    border-top: 1px solid #2c313c;
                }
            """)
        elif theme == "github_dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #0d1117; color: #c9d1d9; }
                QMenuBar { background-color: #161b22; color: #c9d1d9; }
                QMenuBar::item:selected { background-color: #21262d; }
                QToolBar { background-color: #161b22; spacing: 5px; }
                QPushButton {
                    background-color: #238636;
                    color: #ffffff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2ea043; }
                QSplitter::handle { background-color: #21262d; }
                QTabWidget::pane { border: 1px solid #30363d; background-color: #0d1117; }
                QTabBar::tab {
                    background-color: #161b22;
                    color: #c9d1d9;
                    padding: 8px 16px;
                    border: 1px solid #30363d;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #0d1117;
                    border-bottom: 2px solid #f78166;
                }
                QStatusBar {
                    background-color: #f78166;
                    color: #0d1117;
                    border-top: 1px solid #30363d;
                }
            """)
        elif theme == "gruvbox":
            self.setStyleSheet("""
                QMainWindow { background-color: #282828; color: #ebdbb2; }
                QMenuBar { background-color: #3c3836; color: #ebdbb2; }
                QMenuBar::item:selected { background-color: #504945; }
                QToolBar { background-color: #3c3836; spacing: 5px; }
                QPushButton {
                    background-color: #b8bb26;
                    color: #282828;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #d5c4a1; }
                QSplitter::handle { background-color: #504945; }
                QTabWidget::pane { border: 1px solid #504945; background-color: #282828; }
                QTabBar::tab {
                    background-color: #3c3836;
                    color: #ebdbb2;
                    padding: 8px 16px;
                    border: 1px solid #504945;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #282828;
                    border-bottom: 2px solid #fabd2f;
                }
                QStatusBar {
                    background-color: #fabd2f;
                    color: #282828;
                    border-top: 1px solid #504945;
                }
            """)
        else:  # Varsayılan tema (VS Code Dark)
            self.setStyleSheet(self.default_theme_stylesheet())
    def default_theme_stylesheet(self):
        return """
            QMainWindow {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border-bottom: 1px solid #3e3e3e;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #404040;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                spacing: 5px;
            }
            QPushButton {
                background-color: #404040;
                color: #d4d4d4;
                border: 1px solid #555555;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QSplitter::handle {
                background-color: #3e3e3e;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e3e;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 8px 16px;
                border: 1px solid #3e3e3e;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 2px solid #007acc;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
                border-top: 1px solid #3e3e3e;
            }
        """        

    def _init_main_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        self._init_left_panel(main_splitter)

        right_splitter = QSplitter(Qt.Vertical)
        self._init_editor_tabs(right_splitter)
        self._init_console_output(right_splitter)

        right_splitter.setSizes([
            self.WINDOW_HEIGHT - self.CONSOLE_HEIGHT,
            self.CONSOLE_HEIGHT
        ])

        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([
            self.LEFT_PANEL_WIDTH,
            self.WINDOW_WIDTH - self.LEFT_PANEL_WIDTH
        ])


    def _init_left_panel(self, parent_splitter):
        left_panel = QFrame()
        left_panel.setMaximumWidth(self.LEFT_PANEL_WIDTH)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-right: 1px solid #3e3e3e;
            }
        """)

        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Explorer header with refresh button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        explorer_label = QLabel("EXPLORER")
        explorer_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-weight: bold;
                background-color: #2d2d2d;
            }
        """)
        header_layout.addWidget(explorer_label)
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        refresh_btn.clicked.connect(lambda: self.populate_file_tree(os.getcwd()))
        refresh_btn.setToolTip("Refresh file tree")
        header_layout.addWidget(refresh_btn)
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("background-color: #2d2d2d;")
        layout.addWidget(header_widget)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
        """)
        self.file_tree.itemDoubleClicked.connect(self._on_file_tree_double_click)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_explorer_context_menu)
        layout.addWidget(self.file_tree)

        parent_splitter.addWidget(left_panel)
        
        # Set up file system watcher for auto-refresh
        self.project_path = os.getcwd()
        self.fs_watcher = QFileSystemWatcher()
        self._setup_fs_watcher(self.project_path)
        self.fs_watcher.directoryChanged.connect(self._on_directory_changed)
        
        self.populate_file_tree(self.project_path)
        
    def _on_file_tree_double_click(self, item, column):
        """Dosya tree'de double-click yapılınca dosyayı aç"""
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.open_file_from_path(file_path)
    
    def _setup_fs_watcher(self, root_path):
        """File system watcher'ı kurulum - tüm klasörleri izle"""
        try:
            self.fs_watcher.addPath(root_path)
            for dirpath, dirnames, _ in os.walk(root_path):
                # Skip ignored directories
                dirnames[:] = [d for d in dirnames if d not in {'.git', '__pycache__', '.vscode', '.idea', 'node_modules', 'venv', '.env'}]
                for dirname in dirnames:
                    full_path = os.path.join(dirpath, dirname)
                    self.fs_watcher.addPath(full_path)
        except Exception as e:
            print(f"File system watcher setup error: {e}")
    
    def _on_directory_changed(self, path):
        """Klasör değiştiğinde otomatik refresh"""
        # Debounce: Çok sık refresh'i önle
        if hasattr(self, '_refresh_timer'):
            self._refresh_timer.stop()
        else:
            self._refresh_timer = QTimer()
            self._refresh_timer.setSingleShot(True)
            self._refresh_timer.timeout.connect(lambda: self.populate_file_tree(self.project_path))
        self._refresh_timer.start(500)  # 500ms bekle
    
    def _show_explorer_context_menu(self, position):
        """File tree sağ tık menüsü"""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
        """)
        
        item = self.file_tree.itemAt(position)
        
        # Yeni dosya/klasör
        new_file_action = QAction("📄 New File", self)
        new_file_action.triggered.connect(lambda: self._create_new_file(item))
        menu.addAction(new_file_action)
        
        new_folder_action = QAction("📁 New Folder", self)
        new_folder_action.triggered.connect(lambda: self._create_new_folder(item))
        menu.addAction(new_folder_action)
        
        menu.addSeparator()
        
        # Eğer bir item seçiliyse
        if item:
            file_path = item.data(0, Qt.UserRole)
            
            # Rename
            rename_action = QAction("✏️ Rename", self)
            rename_action.triggered.connect(lambda: self._rename_item(item))
            menu.addAction(rename_action)
            
            # Delete
            delete_action = QAction("🗑️ Delete", self)
            delete_action.triggered.connect(lambda: self._delete_item(item))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            # Open in File Explorer
            if file_path:
                open_explorer_action = QAction("📂 Show in Explorer", self)
                open_explorer_action.triggered.connect(lambda: self._open_in_explorer(file_path))
                menu.addAction(open_explorer_action)
        
        menu.exec_(self.file_tree.viewport().mapToGlobal(position))
    
    def _create_new_file(self, parent_item):
        """Yeni dosya oluştur"""
        # Parent klasörü belirle
        if parent_item:
            parent_path = parent_item.data(0, Qt.UserRole)
            if os.path.isfile(parent_path):
                parent_path = os.path.dirname(parent_path)
        else:
            parent_path = self.project_path
        
        # Dosya adı sor
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(parent_path, file_name)
            try:
                # Boş dosya oluştur
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                self.statusBar().showMessage(f"Created: {file_name}")
                # File system watcher otomatik refresh yapacak
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create file:\n{str(e)}")
    
    def _create_new_folder(self, parent_item):
        """Yeni klasör oluştur"""
        # Parent klasörü belirle
        if parent_item:
            parent_path = parent_item.data(0, Qt.UserRole)
            if os.path.isfile(parent_path):
                parent_path = os.path.dirname(parent_path)
        else:
            parent_path = self.project_path
        
        # Klasör adı sor
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            folder_path = os.path.join(parent_path, folder_name)
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.statusBar().showMessage(f"Created folder: {folder_name}")
                # Yeni klasörü watcher'a ekle
                self.fs_watcher.addPath(folder_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create folder:\n{str(e)}")
    
    def _rename_item(self, item):
        """Dosya/klasör yeniden adlandır"""
        old_path = item.data(0, Qt.UserRole)
        old_name = os.path.basename(old_path)
        
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.statusBar().showMessage(f"Renamed: {old_name} → {new_name}")
                # File system watcher otomatik refresh yapacak
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename:\n{str(e)}")
    
    def _delete_item(self, item):
        """Dosya/klasör sil"""
        file_path = item.data(0, Qt.UserRole)
        file_name = os.path.basename(file_path)
        
        # Onay iste
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{file_name}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                self.statusBar().showMessage(f"Deleted: {file_name}")
                # File system watcher otomatik refresh yapacak
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete:\n{str(e)}")
    
    def _open_in_explorer(self, file_path):
        """Dosyayı sistem file explorer'da göster"""
        try:
            if sys.platform == "win32":
                # Windows
                subprocess.Popen(f'explorer /select,"{file_path}"')
            elif sys.platform == "darwin":
                # macOS
                subprocess.Popen(["open", "-R", file_path])
            else:
                # Linux
                subprocess.Popen(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open in explorer:\n{str(e)}")


    def _init_editor_tabs(self, parent_splitter):
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)

        self.add_new_tab()  # İlk sekme
        parent_splitter.addWidget(self.editor_tabs)

    def _init_console_output(self, parent_splitter):
        # Tab widget for console/terminal
        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3e3e3e;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 6px 12px;
                border: 1px solid #3e3e3e;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 2px solid #007acc;
            }
        """)
        
        # Output console tab
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        clear_button = QPushButton("🗑 Temizle")
        clear_button.setFixedHeight(30)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #404040;
                color: red;
            }
        """)
        clear_button.clicked.connect(lambda: self.console.clear())
        header_layout.addStretch()
        header_layout.addWidget(clear_button)
        console_layout.addLayout(header_layout)
        
        self.console = OutputConsole()
        console_layout.addWidget(self.console)
        
        # Terminal tab
        self.terminal = TerminalWidget()
        
        self.bottom_tabs.addTab(console_widget, "Output")
        self.bottom_tabs.addTab(self.terminal, "Terminal")
        
        parent_splitter.addWidget(self.bottom_tabs)

    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        find_action = QAction('🔍 Find & Replace', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self._open_find_replace)
        edit_menu.addAction(find_action)
        
        # Run menu
        run_menu = menubar.addMenu('Run')
        run_action = QAction('▶ Run Python File', self)
        run_action.setShortcut('F5')
        run_action.triggered.connect(self.run_code)
        run_menu.addAction(run_action)
        
        debug_action = QAction('🐛 Debug Mode', self)
        debug_action.setShortcut('Shift+F5')
        debug_action.triggered.connect(self.run_debug)
        run_menu.addAction(debug_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        pip_action = QAction('📦 Paket Yöneticisi (pip)', self)
        pip_action.triggered.connect(self._open_pip_manager)
        tools_menu.addAction(pip_action)
        
        git_action = QAction('🔀 Git Yöneticisi', self)
        git_action.triggered.connect(self._open_git_manager)
        tools_menu.addAction(git_action)

         # Tema Menüsü
        theme_menu = menubar.addMenu("🎨 Theme")

        default_theme = QAction("⚫ Default (VS Code Dark)", self)
        default_theme.triggered.connect(lambda: self._apply_theme("default"))
        theme_menu.addAction(default_theme)

        dracula_theme = QAction("🧛 Dracula", self)
        dracula_theme.triggered.connect(lambda: self._apply_theme("dracula"))
        theme_menu.addAction(dracula_theme)

        nord_theme = QAction("🌊 Nord", self)
        nord_theme.triggered.connect(lambda: self._apply_theme("nord"))
        theme_menu.addAction(nord_theme)

        monokai_theme = QAction("🌙 Monokai", self)
        monokai_theme.triggered.connect(lambda: self._apply_theme("monokai"))
        theme_menu.addAction(monokai_theme)

        solarized_theme = QAction("☀️ Solarized Dark", self)
        solarized_theme.triggered.connect(lambda: self._apply_theme("solarized_dark"))
        theme_menu.addAction(solarized_theme)

        one_dark_theme = QAction("🔵 One Dark (Atom)", self)
        one_dark_theme.triggered.connect(lambda: self._apply_theme("one_dark"))
        theme_menu.addAction(one_dark_theme)

        github_theme = QAction("🐙 GitHub Dark", self)
        github_theme.triggered.connect(lambda: self._apply_theme("github_dark"))
        theme_menu.addAction(github_theme)

        gruvbox_theme = QAction("🟤 Gruvbox", self)
        gruvbox_theme.triggered.connect(lambda: self._apply_theme("gruvbox"))
        theme_menu.addAction(gruvbox_theme)
        
    def setup_toolbar(self):
        toolbar = self.addToolBar('Main')
        toolbar.setMovable(False)
        
        # File operations
        new_btn = QPushButton('New')
        new_btn.clicked.connect(self.new_file)
        toolbar.addWidget(new_btn)
        
        open_btn = QPushButton('Open')
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)
        
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self.save_file)
        toolbar.addWidget(save_btn)
        
        toolbar.addSeparator()
        
        # Run button 
        run_btn = QPushButton('▶ Run')
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #16825d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a9867;
            }
        """)
        run_btn.clicked.connect(self.run_code)
        toolbar.addWidget(run_btn)

    def setup_statusbar(self):
        self.statusBar().showMessage('PyIDE Ready | Created by Mert Ulupınar 🚀')

    def add_new_tab(self, filename="Untitled"):
        editor = ModernCodeEditor()
        tab_index = self.editor_tabs.addTab(editor, filename)
        self.editor_tabs.setCurrentIndex(tab_index)
        return editor

    def close_tab(self, index):
        # Tab'ı kapatırken dosya yolunu da temizle
        if index in self.tab_file_paths:
            del self.tab_file_paths[index]
            
        if self.editor_tabs.count() > 1:
            self.editor_tabs.removeTab(index)
            # Index'leri yeniden düzenle
            self.tab_file_paths = {
                i if i < index else i-1: path 
                for i, path in self.tab_file_paths.items()
            }
        else:
            # Son tab'ı kapatma, sadece temizle
            current_editor = self.editor_tabs.currentWidget()
            if current_editor:
                current_editor.clear()

    def get_current_editor(self):
        return self.editor_tabs.currentWidget()

    def new_file(self):
        self.add_new_tab()

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 
                                                  'Python Files (*.py);;All Files (*)')
        if filename:
            self.open_file_from_path(filename)
            
    def open_file_from_path(self, filename):
        """Belirtilen dosyayı aç (file tree'den veya dialog'dan)"""
        # Dosya zaten açıksa o tab'a geç
        for tab_idx, path in self.tab_file_paths.items():
            if path == filename:
                self.editor_tabs.setCurrentIndex(tab_idx)
                return
                
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            
            editor = self.add_new_tab(os.path.basename(filename))
            editor.setPlainText(content)
            tab_idx = self.editor_tabs.currentIndex()
            self.tab_file_paths[tab_idx] = filename
            self.statusBar().showMessage(f'Opened: {filename}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not open file:\n{str(e)}')

    def save_file(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            return
        
        current_tab_idx = self.editor_tabs.currentIndex()
        current_file = self.tab_file_paths.get(current_tab_idx)
            
        if current_file:
            try:
                with open(current_file, 'w', encoding='utf-8') as file:
                    file.write(current_editor.toPlainText())
                self.statusBar().showMessage(f'Saved: {current_file}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Could not save file:\n{str(e)}')
        else:
            self.save_as_file()

    def save_as_file(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 
                                                  'Python Files (*.py);;All Files (*)')
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(current_editor.toPlainText())
                current_tab_idx = self.editor_tabs.currentIndex()
                self.tab_file_paths[current_tab_idx] = filename
                self.editor_tabs.setTabText(current_tab_idx, os.path.basename(filename))
                self.statusBar().showMessage(f'Saved: {filename}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Could not save file:\n{str(e)}')

        #icon functions
    def populate_file_tree(self, root_path):
        """Dosya ağacını optimize edilmiş şekilde doldur"""
        self.file_tree.clear()
        
        # File system watcher'ı yeniden kur
        if hasattr(self, 'fs_watcher'):
            # Eski path'leri temizle
            old_paths = self.fs_watcher.directories()
            if old_paths:
                self.fs_watcher.removePaths(old_paths)
            # Yeni path'leri ekle
            self._setup_fs_watcher(root_path)
        
        SKIP_DIRS = {'.git', '__pycache__', '.vscode', '.idea', 'node_modules', 'venv', '.env'}
        SHOW_EXTENSIONS = {'.py', '.txt', '.md', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'}

        def add_items(parent_item, path):
            try:
                items = sorted(os.listdir(path))
            except PermissionError:
                return
                
            for name in items:
                if name.startswith('.') and name not in {'.gitignore'}:
                    continue
                    
                full_path = os.path.join(path, name)
                is_dir = os.path.isdir(full_path)

                if is_dir and name in SKIP_DIRS:
                    continue
                    
                if not is_dir and not any(name.endswith(ext) for ext in SHOW_EXTENSIONS):
                    continue

                icon = QIcon(self.ICON_FOLDER) if is_dir else self._get_icon_for_file(name)

                item = QTreeWidgetItem([name])
                item.setIcon(0, icon)
                item.setData(0, Qt.UserRole, full_path)

                parent_item.addChild(item)

                if is_dir:
                    add_items(item, full_path)

        root_item = QTreeWidgetItem([os.path.basename(root_path)])
        root_item.setIcon(0, QIcon(self.ICON_FOLDER))
        self.file_tree.addTopLevelItem(root_item)
        add_items(root_item, root_path)
        root_item.setExpanded(True)

        #select by file type
    def _get_icon_for_file(self, filename):
        if filename.endswith(".py"):
            return QIcon(self.ICON_PYTHON)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            return QIcon(self.ICON_FILE)
        else:
            return QIcon(self.ICON_FILE)

    def run_code(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            return

        code = current_editor.toPlainText().strip()
        if not code:
            self.console.setText("Çalıştırılacak kod yok!")
            return

        self.console.clear()
        self.console.append("Python kodu çalıştırılıyor...\n" + "=" * 50)

        try:
            # Kodu geçici dosyaya kaydet
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # Input varsa yeni console penceresi aç, yoksa arka planda çalıştır
            if "input(" in code:
                self.console.append("\n<b style='color:#4caf50'>→ Kod yeni konsol penceresinde çalıştırılıyor...</b>")
                self.console.append("<i>Program tamamlanınca konsol penceresi kapanacak.</i>\n")
                
                if sys.platform == "win32":
                    # Windows: cmd ile aç - sys.executable kullan
                    python_exe = sys.executable.replace('\\', '/')
                    subprocess.Popen(
                        f'start cmd /k ""{python_exe}" "{temp_file_path}" & echo. & echo Program tamamlandi. Kapatmak icin bir tusa basin... & pause > nul & exit"',
                        shell=True
                    )
                else:
                    # Linux/Mac: terminal ile aç
                    subprocess.Popen(['x-terminal-emulator', '-e', f'{sys.executable} {temp_file_path}; read -p "Press enter to close..."'])
                
                self.statusBar().showMessage("Kod yeni konsol penceresinde çalışıyor")
                
            else:
                # Input yoksa arka planda çalıştır ve çıktıyı göster
                current_editor.clear_error_lines()  # Önceki hataları temizle
                
                process = subprocess.Popen(
                    [sys.executable, temp_file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )

                output, error = process.communicate(timeout=30)

                if output:
                    self.console.append(f"\n<b>Çıktı:</b>\n{output}")
                if error:
                    self.console.append(f"\n<b style='color:#f44336'>Hatalar:</b>\n{error}")
                    # Hata satırlarını parse et
                    error_lines = self._parse_error_lines(error, current_editor.toPlainText())
                    if error_lines:
                        current_editor.set_error_lines(error_lines)
                        self.console.append(f"\n<i>→ Hata satırları vurgulandı: {', '.join(map(str, error_lines))}</i>")
                        
                if not output and not error:
                    self.console.append("\n<b style='color:#4caf50'>✓ Kod başarıyla çalıştı (çıktı yok)</b>")

                self.statusBar().showMessage("Kod çalıştırma tamamlandı")
                
            # Geçici dosyayı sil (biraz bekle)
            def cleanup():
                time.sleep(2)
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            from threading import Thread
            Thread(target=cleanup, daemon=True).start()

        except subprocess.TimeoutExpired:
            process.kill()
            self.console.append("\n<b style='color:#f44336'>Hata: Kod çalıştırma zaman aşımına uğradı (30 saniye)</b>")
        except Exception as e:
            self.console.append(f"\n<b style='color:#f44336'>Beklenmeyen hata:</b> {str(e)}")
            self.statusBar().showMessage("Hata oluştu")
    
    def _parse_error_lines(self, error_text, code):
        """Hata metninden satır numaralarını çıkar"""
        error_lines = []
        # Pattern: line X veya File "...", line X
        patterns = [
            r'line (\d+)',
            r'File ".*?", line (\d+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, error_text)
            for match in matches:
                line_num = int(match.group(1))
                # Kod satır sayısından fazla değilse ekle
                if 1 <= line_num <= code.count('\n') + 1:
                    error_lines.append(line_num)
        
        return sorted(set(error_lines))  # Tekrarları kaldır ve sırala
    
    def _open_find_replace(self):
        """Find & Replace dialog'u aç"""
        current_editor = self.get_current_editor()
        if current_editor:
            dialog = FindReplaceDialog(current_editor, self)
            dialog.show()  # Modeless dialog
    
    def _open_pip_manager(self):
        """Pip manager dialog'u aç"""
        dialog = PipManagerDialog(self)
        dialog.exec_()
    
    def _open_git_manager(self):
        """Git manager dialog'u aç"""
        dialog = GitManagerDialog(self)
        dialog.exec_()
    
    def run_debug(self):
        """Kodu debug modunda çalıştır (pdb ile)"""
        current_editor = self.get_current_editor()
        if not current_editor:
            return

        code = current_editor.toPlainText().strip()
        if not code:
            self.console.setText("Çalıştırılacak kod yok!")
            return

        self.console.clear()
        self.console.append("🐛 Debug Mode: Python Debugger (pdb) başlatılıyor...")
        self.console.append("=" * 50)
        self.console.append("\n<b>Debug Komutları:</b>")
        self.console.append("  <b>n</b> (next) - Sonraki satıra geç")
        self.console.append("  <b>s</b> (step) - Fonksiyon içine gir")
        self.console.append("  <b>c</b> (continue) - Devam et")
        self.console.append("  <b>l</b> (list) - Kodu göster")
        self.console.append("  <b>p</b> değişken - Değişken değerini yazdır")
        self.console.append("  <b>q</b> (quit) - Çık\n")

        try:
            # Kodu geçici dosyaya kaydet
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # pdb ile debug modunda terminal aç
            self.console.append("<b style='color:#ff9800'>→ Debug konsolu yeni pencerede açılıyor...</b>\n")
            
            if sys.platform == "win32":
                python_exe = sys.executable.replace('\\', '/')
                subprocess.Popen(
                    f'start cmd /k ""{python_exe}" -m pdb "{temp_file_path}""',
                    shell=True
                )
            else:
                subprocess.Popen(['x-terminal-emulator', '-e', f'{sys.executable} -m pdb {temp_file_path}'])
            
            self.statusBar().showMessage("Debug modu: pdb konsolu açıldı")
            
            # Geçici dosyayı daha geç sil
            def cleanup():
                time.sleep(10)
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            from threading import Thread
            Thread(target=cleanup, daemon=True).start()

        except Exception as e:
            self.console.append(f"\n<b style='color:#f44336'>Hata:</b> {str(e)}")
            self.statusBar().showMessage("Debug başlatma hatası")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the IDE
    ide = ModernPythonIDE()
    ide.show()
    
    sys.exit(app.exec_())