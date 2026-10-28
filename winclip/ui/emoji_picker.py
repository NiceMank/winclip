"""Sélecteur d'émojis et symboles façon Windows 11."""
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QScrollArea, QLineEdit, QLabel
)
from ..config import THEME

EMOJI_CATEGORIES = {
    "Visages & Émotions": [
        "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🙂", "🙃",
        "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😋",
        "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐",
        "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥", "😌",
        "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮", "🤧",
        "🥵", "🥶", "🥴", "😵", "🤯", "🤠", "🥳", "😎", "🤓", "🧐"
    ],
    "Gestes & Mains": [
        "👍", "👎", "👊", "✊", "🤛", "🤜", "👏", "🙌", "👐", "🤲",
        "🤝", "🙏", "✍️", "💅", "🤳", "💪", "✌️", "🤞", "🤟", "🤘",
        "👌", "🤌", "🤏", "👈", "👉", "👆", "👇", "☝️", "✋", "🤚"
    ],
    "Tech & Outils": [
        "💻", "🖥️", "⌨️", "🖱️", "🖨️", "💾", "📱", "📲", "🔋", "🔌",
        "💡", "🔦", "⚙️", "🔧", "🔨", "🛠️", "🧰", "🚀", "⚡", "🔥",
        "🛡️", "🔑", "🔒", "🔓", "🔍", "🔎", "📡", "🛰️", "🧪", "🧬"
    ],
    "Symboles & Typo": [
        "✓", "✔", "✕", "✖", "★", "☆", "•", "→", "←", "↑", "↓", "↔",
        "➜", "➤", "©", "®", "™", "€", "$", "£", "¥", "₿", "±", "≠",
        "≤", "≥", "≈", "∞", "π", "√", "∑", "∫", "♥", "♦", "♣", "♠",
        "⚠️", "⛔", "✅", "❌", "❓", "❗", "💬", "💭", "📢", "🔔"
    ]
}


class EmojiPickerWidget(QWidget):
    emoji_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Barre de défilement contenant les catégories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.categories_layout = QVBoxLayout(content_widget)
        self.categories_layout.setContentsMargins(4, 4, 4, 4)
        self.categories_layout.setSpacing(16)

        for cat_name, emojis in EMOJI_CATEGORIES.items():
            cat_header = QLabel(cat_name)
            cat_header.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 12px; font-weight: 600; padding: 2px 0;")
            self.categories_layout.addWidget(cat_header)

            grid = QGridLayout()
            grid.setSpacing(4)
            cols = 8

            for idx, em in enumerate(emojis):
                btn = QPushButton(em)
                btn.setProperty("class", "EmojiButton")
                btn.setFixedSize(38, 38)
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn.setToolTip(f"Insérer {em}")
                btn.clicked.connect(lambda checked, char=em: self.emoji_selected.emit(char))
                row = idx // cols
                col = idx % cols
                grid.addWidget(btn, row, col)

            self.categories_layout.addLayout(grid)

        self.categories_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
