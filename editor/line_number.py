from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import Qt, QSize

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

