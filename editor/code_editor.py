from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QCompleter
from PyQt5.QtGui import QColor, QFont, QTextCursor, QTextFormat
from PyQt5.QtCore import Qt, QRect, QTimer, QStringListModel

try:
    import jedi
    JEDI_AVAILABLE = True
except ImportError:
    JEDI_AVAILABLE = False

from core.highlighter import Pide
from editor.line_number import LineNumberArea
from editor.minimap import Minimap

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
        self.fallback_words = sorted(set(keywords + builtins + modules))
        
        # QCompleter oluştur
        self.completer = QCompleter(self.fallback_words)
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
    
    def _update_jedi_completions(self):
        if not JEDI_AVAILABLE:
            return
            
        code = self.toPlainText()
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber()
        
        try:
            script = jedi.Script(code)
            completions = script.complete(line, column)
            words = [c.name for c in completions]
            
            if words:
                words.extend(self.snippets.keys())
                words = sorted(list(set(words)))
                model = QStringListModel(words)
                self.completer.setModel(model)
            else:
                self.completer.setModel(QStringListModel(self.fallback_words))
        except Exception:
            self.completer.setModel(QStringListModel(self.fallback_words))

    def _show_autocomplete(self):
        """Autocomplete popup'ı göster"""
        self._update_jedi_completions()
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
        
        self._update_jedi_completions()
        
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

