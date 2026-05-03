from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QFont, QPainter, QTextCursor
from PyQt5.QtCore import Qt

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

