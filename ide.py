import sys
import os
import subprocess
import ast
import importlib
import tempfile
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPlainTextEdit, QTextEdit, QPushButton,
    QLabel, QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog, QAction, QTabWidget,
    QToolBar, QMenuBar, QMessageBox, QFrame, QTreeWidget, QTreeWidgetItem,QInputDialog
)

from PyQt5.QtGui import (  
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextCursor, QPainter, QTextFormat,QIcon
)

from PyQt5.QtCore import QRegExp, Qt, QRect, QSize, QTimer

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


class ModernCodeEditor(QPlainTextEdit):
    INDENT_SIZE = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self._setup_appearance()
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

    def _connect_signals(self):
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self._on_text_changed)
        
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
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        self.line_number_area.paintEvent(event)

    def highlight_current_line(self):
        if self.isReadOnly():
            return

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(46, 46, 46, 100))
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        self.setExtraSelections([selection])

    def keyPressEvent(self, event):
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
        self.setWindowTitle("PyIDE")
        self.setGeometry(100, 100, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        # UI kur
        self._apply_theme()
        self._init_main_layout()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()


    def _apply_theme(self,theme='default'):
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
        else:  # Varsayılan tema
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

        explorer_label = QLabel("EXPLORER")
        explorer_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-weight: bold;
                padding: 10px;
                background-color: #2d2d2d;
            }
        """)
        layout.addWidget(explorer_label)

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
        layout.addWidget(self.file_tree)

        parent_splitter.addWidget(left_panel)
        project_path = os.getcwd()
        self.populate_file_tree(project_path)
        
    def _on_file_tree_double_click(self, item, column):
        """Dosya tree'de double-click yapılınca dosyayı aç"""
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.open_file_from_path(file_path)


    def _init_editor_tabs(self, parent_splitter):
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)

        self.add_new_tab()  # İlk sekme
        parent_splitter.addWidget(self.editor_tabs)

    def _init_console_output(self, parent_splitter):
        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)

        # Header (label + clear button)
        header_layout = QHBoxLayout()
        console_label = QLabel("OUTPUT")
        console_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-weight: bold;
                padding: 5px 10px;
                background-color: #2d2d2d;
                border-bottom: 1px solid #3e3e3e;
            }
        """)
        clear_button = QPushButton("🗑")
        clear_button.setFixedSize(40, 30)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                color: red;
            }
        """)
        clear_button.clicked.connect(lambda: self.console.clear())

        header_layout.addWidget(console_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_button)

        console_layout.addLayout(header_layout)

        # Console
        self.console = OutputConsole()
        console_layout.addWidget(self.console)

        parent_splitter.addWidget(console_container)

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
        
        # Run menu
        run_menu = menubar.addMenu('Run')
        run_action = QAction('Run Python File', self)
        run_action.setShortcut('F5')
        run_action.triggered.connect(self.run_code)
        run_menu.addAction(run_action)

         # Tema Menüsü
        theme_menu = menubar.addMenu("Tema")

        default_theme = QAction("Varsayılan", self)
        default_theme.triggered.connect(lambda: self._apply_theme("default"))
        theme_menu.addAction(default_theme)

        dracula_theme = QAction("Dracula", self)
        dracula_theme.triggered.connect(lambda: self._apply_theme("dracula"))
        theme_menu.addAction(dracula_theme)

        nord_theme = QAction("Nord", self)
        nord_theme.triggered.connect(lambda: self._apply_theme("nord"))
        theme_menu.addAction(nord_theme)
        
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
        self.statusBar().showMessage('Ready')

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the IDE
    ide = ModernPythonIDE()
    ide.show()
    
    sys.exit(app.exec_())