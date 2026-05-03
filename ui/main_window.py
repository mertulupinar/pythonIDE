import sys
import os
import subprocess
import tempfile
import time
import re
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QAction, QTabWidget, QMessageBox, QFrame,
    QTreeWidget, QTreeWidgetItem, QInputDialog, QMenu
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QFileSystemWatcher, QProcess

from editor.code_editor import ModernCodeEditor
from widgets.console import OutputConsole
from widgets.terminal import TerminalWidget
from dialogs.find_replace import FindReplaceDialog
from managers.git_manager import GitManagerDialog
from managers.pip_manager import PipManagerDialog

class ModernPythonIDE(QMainWindow):
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    LEFT_PANEL_WIDTH = 250
    CONSOLE_HEIGHT = 200

    def __init__(self):
        super().__init__()

        # Dinamik base path (proje ana dizini)
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Taşınabilir ikon yolları
        self.ICON_FOLDER = os.path.join(self.BASE_DIR, "icons", "folder.png")
        self.ICON_PYTHON = os.path.join(self.BASE_DIR, "icons", "python.png")
        self.ICON_FILE   = os.path.join(self.BASE_DIR, "icons", "file.png")

        # Pencere ayarları
        self.tab_file_paths = {}  # {id(editor_widget): dosya_yolu} — widget referansı bazlı
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
        refresh_btn.clicked.connect(lambda: self.populate_file_tree(self.project_path))
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
        self.editor_tabs.currentChanged.connect(self._on_tab_changed)

        self.add_new_tab()  # İlk sekme
        parent_splitter.addWidget(self.editor_tabs)
        
    def _on_tab_changed(self, index):
        """Aktif sekme değiştiğinde explorer'ı o dosyanın dizinine güncelle"""
        editor = self.editor_tabs.widget(index)
        if editor and id(editor) in self.tab_file_paths:
            file_path = self.tab_file_paths[id(editor)]
            new_dir = os.path.dirname(os.path.abspath(file_path))
            if hasattr(self, 'project_path') and self.project_path != new_dir:
                self.project_path = new_dir
                self.populate_file_tree(new_dir)

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
        clear_button = QPushButton("🗑 Clear")
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
        
        stop_action = QAction('⏹ Stop', self)
        stop_action.setShortcut('Ctrl+Shift+F5')
        stop_action.triggered.connect(self.stop_code)
        run_menu.addAction(stop_action)
        
        run_menu.addSeparator()
        
        debug_action = QAction('🐛 Debug Mode', self)
        debug_action.setShortcut('Shift+F5')
        debug_action.triggered.connect(self.run_debug)
        run_menu.addAction(debug_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        pip_action = QAction('📦 Package Manager (pip)', self)
        pip_action.triggered.connect(self._open_pip_manager)
        tools_menu.addAction(pip_action)
        
        git_action = QAction('🔀 Git Manager', self)
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
        
        # Stop button
        stop_btn = QPushButton('⏹ Stop')
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        stop_btn.clicked.connect(self.stop_code)
        toolbar.addWidget(stop_btn)

    def setup_statusbar(self):
        self.statusBar().showMessage('PyIDE Ready | Created by Mert Ulupınar 🚀')

    def add_new_tab(self, filename="Untitled"):
        editor = ModernCodeEditor()
        tab_index = self.editor_tabs.addTab(editor, filename)
        self.editor_tabs.setCurrentIndex(tab_index)
        return editor

    def close_tab(self, index):
        # Tab'ı kapatırken dosya yolunu da temizle
        editor = self.editor_tabs.widget(index)
        if editor and id(editor) in self.tab_file_paths:
            del self.tab_file_paths[id(editor)]
            
        if self.editor_tabs.count() > 1:
            self.editor_tabs.removeTab(index)
        else:
            # Son tab'ı kapatma, sadece temizle
            current_editor = self.editor_tabs.currentWidget()
            if current_editor:
                current_editor.clear()
                # Son tab'ın dosya yolunu da temizle
                if id(current_editor) in self.tab_file_paths:
                    del self.tab_file_paths[id(current_editor)]

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
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            if editor and self.tab_file_paths.get(id(editor)) == filename:
                self.editor_tabs.setCurrentIndex(i)
                return
                
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            
            editor = self.add_new_tab(os.path.basename(filename))
            editor.setPlainText(content)
            self.tab_file_paths[id(editor)] = filename
            self.statusBar().showMessage(f'Opened: {filename}')
            
            # Açılan dosyanın dizinine göre File Explorer'ı güncelle
            new_dir = os.path.dirname(os.path.abspath(filename))
            if hasattr(self, 'project_path') and self.project_path != new_dir:
                self.project_path = new_dir
                self.populate_file_tree(new_dir)
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not open file:\n{str(e)}')

    def save_file(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            return
        
        current_file = self.tab_file_paths.get(id(current_editor))
            
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
                self.tab_file_paths[id(current_editor)] = filename
                current_tab_idx = self.editor_tabs.currentIndex()
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

        # Zaten çalışan bir process varsa durdur
        if hasattr(self, '_run_process') and self._run_process and self._run_process.state() != QProcess.NotRunning:
            self._run_process.kill()
            self._run_process.waitForFinished(1000)

        self.console.clear()
        self.console.append("Python kodu çalıştırılıyor...\n" + "=" * 50)

        try:
            current_file = self.tab_file_paths.get(id(current_editor))
            self._run_is_temp = False

            if current_file and os.path.exists(current_file):
                # Dosyayı kaydet ve orijinal yolunu kullan
                try:
                    with open(current_file, 'w', encoding='utf-8') as file:
                        file.write(code)
                except Exception as e:
                    self.console.append(f"\n<b style='color:#f44336'>Dosya kaydedilirken hata:</b> {str(e)}")
                    return
                self._run_target_path = current_file
                cwd = os.path.dirname(current_file)
            else:
                # Kodu geçici dosyaya kaydet
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(code)
                    self._run_target_path = temp_file.name
                self._run_is_temp = True
                cwd = os.getcwd()

            # Input varsa yeni console penceresi aç, yoksa arka planda çalıştır
            if "input(" in code:
                self.console.append("\n<b style='color:#4caf50'>→ Kod yeni konsol penceresinde çalıştırılıyor...</b>")
                self.console.append("<i>Program tamamlanınca konsol penceresi kapanacak.</i>\n")
                
                if sys.platform == "win32":
                    python_exe = sys.executable.replace('\\', '/')
                    subprocess.Popen(
                        f'start cmd /k ""{python_exe}" "{self._run_target_path}" & echo. & echo Program tamamlandi. Kapatmak icin bir tusa basin... & pause > nul & exit"',
                        shell=True, cwd=cwd
                    )
                else:
                    subprocess.Popen(['x-terminal-emulator', '-e', f'{sys.executable} {self._run_target_path}; read -p "Press enter to close..."'], cwd=cwd)
                
                self.statusBar().showMessage("Kod yeni konsol penceresinde çalışıyor")
                
            else:
                # --- Asenkron çalıştırma (QProcess) ---
                current_editor.clear_error_lines()
                
                self._run_process = QProcess(self)
                self._run_process.setWorkingDirectory(cwd)
                self._run_stdout = ""
                self._run_stderr = ""
                self._run_editor = current_editor
                
                # Sinyalleri bağla
                self._run_process.readyReadStandardOutput.connect(self._on_run_stdout)
                self._run_process.readyReadStandardError.connect(self._on_run_stderr)
                self._run_process.finished.connect(self._on_run_finished)
                self._run_process.errorOccurred.connect(self._on_run_error)
                
                # Süre sayacı
                self._run_elapsed = 0
                self._run_timer = QTimer(self)
                self._run_timer.timeout.connect(self._on_run_tick)
                self._run_timer.start(1000)
                
                # Statusbar'da "çalışıyor" göster
                self.statusBar().showMessage("⏳ Kod çalışıyor... (0s)")
                
                # Process'i başlat
                self._run_process.start(sys.executable, [self._run_target_path])

        except Exception as e:
            self.console.append(f"\n<b style='color:#f44336'>Beklenmeyen hata:</b> {str(e)}")
            self.statusBar().showMessage("Hata oluştu")
    
    def stop_code(self):
        """Çalışan kodu durdur"""
        if hasattr(self, '_run_process') and self._run_process and self._run_process.state() != QProcess.NotRunning:
            self._run_process.kill()
            self.console.append("\n<b style='color:#ff9800'>⚠ Program kullanıcı tarafından durduruldu.</b>")
            self.statusBar().showMessage("Program durduruldu")
    
    def _on_run_stdout(self):
        """Stdout verisi geldiğinde canlı olarak konsola yaz"""
        data = self._run_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self._run_stdout += data
        self.console.insertPlainText(data)
    
    def _on_run_stderr(self):
        """Stderr verisi geldiğinde canlı olarak konsola yaz"""
        data = self._run_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self._run_stderr += data
        self.console.append(f"<span style='color:#f44336'>{data}</span>")
    
    def _on_run_tick(self):
        """Her saniye süre sayacını güncelle"""
        self._run_elapsed += 1
        self.statusBar().showMessage(f"⏳ Kod çalışıyor... ({self._run_elapsed}s)")
    
    def _on_run_error(self, error):
        """QProcess hata oluştuğunda"""
        error_messages = {
            QProcess.FailedToStart: "Program başlatılamadı. Python yolu kontrol edin.",
            QProcess.Crashed: "Program beklenmedik şekilde çöktü.",
            QProcess.Timedout: "Program zaman aşımına uğradı.",
        }
        msg = error_messages.get(error, f"Bilinmeyen hata: {error}")
        self.console.append(f"\n<b style='color:#f44336'>Hata:</b> {msg}")
    
    def _on_run_finished(self, exit_code, exit_status):
        """Process tamamlandığında sonuçları göster"""
        # Süre sayacını durdur
        if hasattr(self, '_run_timer') and self._run_timer:
            self._run_timer.stop()
        
        elapsed = self._run_elapsed if hasattr(self, '_run_elapsed') else 0
        
        # Sonuç mesajı
        if exit_code == 0 and not self._run_stderr:
            if not self._run_stdout:
                self.console.append("\n<b style='color:#4caf50'>✓ Kod başarıyla çalıştı (çıktı yok)</b>")
            self.console.append(f"\n<b style='color:#4caf50'>✓ Tamamlandı ({elapsed}s)</b>")
        else:
            if self._run_stderr:
                # Hata satırlarını parse et ve editörde vurgula
                error_lines = self._parse_error_lines(self._run_stderr, self._run_editor.toPlainText())
                if error_lines:
                    self._run_editor.set_error_lines(error_lines)
                    self.console.append(f"\n<i>→ Hata satırları vurgulandı: {', '.join(map(str, error_lines))}</i>")
            
            if exit_status == QProcess.CrashExit:
                self.console.append(f"\n<b style='color:#f44336'>✗ Program çöktü ({elapsed}s)</b>")
            else:
                self.console.append(f"\n<b style='color:#ff9800'>⚠ Çıkış kodu: {exit_code} ({elapsed}s)</b>")
        
        self.statusBar().showMessage(f"Kod çalıştırma tamamlandı ({elapsed}s)")
        
        # Geçici dosyayı temizle
        if self._run_is_temp:
            QTimer.singleShot(2000, lambda: self._cleanup_temp(self._run_target_path))
    
    def _cleanup_temp(self, path):
        """Geçici dosyayı sil"""
        try:
            os.unlink(path)
        except:
            pass
    
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
            current_file = self.tab_file_paths.get(id(current_editor))
            is_temp = False

            if current_file and os.path.exists(current_file):
                try:
                    with open(current_file, 'w', encoding='utf-8') as file:
                        file.write(code)
                except Exception as e:
                    self.console.append(f"\n<b style='color:#f44336'>Dosya kaydedilirken hata:</b> {str(e)}")
                    return
                target_path = current_file
                cwd = os.path.dirname(current_file)
            else:
                # Kodu geçici dosyaya kaydet
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(code)
                    target_path = temp_file.name
                is_temp = True
                cwd = os.getcwd()

            # pdb ile debug modunda terminal aç
            self.console.append("<b style='color:#ff9800'>→ Debug konsolu yeni pencerede açılıyor...</b>\n")
            
            if sys.platform == "win32":
                python_exe = sys.executable.replace('\\', '/')
                subprocess.Popen(
                    f'start cmd /k ""{python_exe}" -m pdb "{target_path}""',
                    shell=True, cwd=cwd
                )
            else:
                subprocess.Popen(['x-terminal-emulator', '-e', f'{sys.executable} -m pdb {target_path}'], cwd=cwd)
            
            self.statusBar().showMessage("Debug modu: pdb konsolu açıldı")
            
            if is_temp:
                # Geçici dosyayı daha geç sil
                def cleanup():
                    time.sleep(10)
                    try:
                        os.unlink(target_path)
                    except:
                        pass
                
                from threading import Thread
                Thread(target=cleanup, daemon=True).start()

        except Exception as e:
            self.console.append(f"\n<b style='color:#f44336'>Hata:</b> {str(e)}")
            self.statusBar().showMessage("Debug başlatma hatası")

