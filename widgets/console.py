from PyQt5.QtWidgets import QTextEdit

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

