import sys
import subprocess
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QTextEdit, QProgressBar, QMessageBox
)

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

