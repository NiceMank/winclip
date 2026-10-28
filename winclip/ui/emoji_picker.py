"""Sélecteur d'émojis et symboles façon Windows 11.

Nouveautés v2 :
  - section « Récents » persistée (préférences utilisateur) ;
  - 11 catégories enrichies (~380 émojis et symboles) ;
  - grille adaptative et boutons plus larges.
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QScrollArea, QLabel
)

from ..i18n import tr
from ..settings import settings

EMOJI_CATEGORIES: dict[str, list[str]] = {
    "cat_faces": [
        "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🙂", "🙃",
        "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😋",
        "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐",
        "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥", "😌",
        "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮", "🤧",
        "🥵", "🥶", "🥴", "😵", "🤯", "🤠", "🥳", "😎", "🤓", "🧐",
    ],
    "cat_gestures": [
        "👍", "👎", "👊", "✊", "🤛", "🤜", "👏", "🙌", "👐", "🤲",
        "🤝", "🙏", "✍️", "💅", "🤳", "💪", "✌️", "🤞", "🤟", "🤘",
        "👌", "🤌", "🤏", "👈", "👉", "👆", "👇", "☝️", "✋", "🤚",
        "🖐️", "🖖", "👋", "🤙", "💪", "🦾", "🫰", "🫵", "🫶", "🤟",
    ],
    "cat_hearts": [
        "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
        "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "♥️",
        "💌", "💋", "🥹", "😻",
    ],
    "cat_animals": [
        "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
        "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🐤", "🦆",
        "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋",
        "🐌", "🐞", "🐜", "🦟", "🐢", "🐍", "🦖", "🐙", "🦀", "🐬",
    ],
    "cat_food": [
        "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🫐", "🍈",
        "🍒", "🍑", "🥭", "🍍", "🥥", "🥝", "🍅", "🥑", "🍞", "🥐",
        "🧀", "🍕", "🍔", "🍟", "🌭", "🍿", "🥤", "☕", "🍺", "🍷",
        "🎂", "🍰",
    ],
    "cat_activities": [
        "⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🎱", "🏓", "🏸",
        "🥅", "⛳", "🏹", "🎣", "🥊", "🥋", "🎽", "🛹", "🛼", "⛸️",
        "🎿", "🏂", "🏋️", "🤸",
    ],
    "cat_travel": [
        "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑", "🚒", "🚐",
        "🛻", "🚚", "🚲", "🛴", "🏍️", "🛵", "🚨", "🚔", "🚍", "🚘",
        "🚖", "🚡", "🚠", "🚃", "🚋", "🚞", "🚝", "🚄", "🚅", "🚈",
        "🚁", "✈️",
    ],
    "cat_objects": [
        "⌚", "📱", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "💽", "💾", "💿",
        "📀", "📷", "📹", "🎥", "🎞️", "📞", "☎️", "📟", "📠", "📺",
        "📻", "🎙️", "🧭", "⏰", "⏳", "📡", "🔋", "🔌", "💡", "🔦",
        "🕯️", "🧳",
    ],
    "cat_tech": [
        "🚀", "⚡", "🔥", "✨", "🛡️", "🔑", "🔒", "🔓", "🔍", "🔎",
        "🛰️", "🧪", "🧬", "⚙️", "🔧", "🔨", "🛠️", "🧰", "🧲", "💉",
        "🩺", "🧿", "🎛️", "🎚️", "🕹️", "🎮", "👾", "🤖", "💣", "🔔",
    ],
    "cat_symbols": [
        "✓", "✔", "✕", "✖", "★", "☆", "•", "◦", "©", "®",
        "™", "€", "$", "£", "¥", "₿", "±", "≠", "≤", "≥",
        "≈", "∞", "π", "√", "∑", "∫", "♥", "♦", "♣", "♠",
        "⚠️", "⛔", "✅", "❌", "❓", "❗", "💬", "💭", "📢", "🔊",
        "⏏", "⌛", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪",
    ],
    "cat_arrows": [
        "←", "↑", "→", "↓", "↔", "↕", "↖", "↗", "↘", "↙",
        "↺", "↻", "⇒", "⇐", "⇑", "⇓", "⇔", "➜", "➤", "⬅",
        "⬆", "⬇", "▶", "◀",
    ],
}

GRID_COLS = 8


class EmojiPickerWidget(QWidget):
    emoji_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.categories_layout = QVBoxLayout(content_widget)
        self.categories_layout.setContentsMargins(4, 2, 4, 4)
        self.categories_layout.setSpacing(12)

        # --- Section « Récents » (recréée dynamiquement) ---
        self.recents_container = QWidget()
        self.recents_container.setStyleSheet("background: transparent;")
        self.recents_layout = QVBoxLayout(self.recents_container)
        self.recents_layout.setContentsMargins(0, 0, 0, 0)
        self.recents_layout.setSpacing(4)
        self.categories_layout.addWidget(self.recents_container)
        self._build_recents()

        # --- Catégories fixes ---
        for cat_key, emojis in EMOJI_CATEGORIES.items():
            self.categories_layout.addWidget(self._make_header(cat_key))
            grid = self._make_grid(emojis)
            self.categories_layout.addLayout(grid)

        self.categories_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    # ------------------------------------------------------------------
    def _make_header(self, title_key: str) -> QLabel:
        header = QLabel(tr(title_key))
        header.setProperty("class", "CategoryHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        return header

    def _make_grid(self, emojis: list[str]) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)
        for idx, em in enumerate(emojis):
            btn = self._make_button(em)
            grid.addWidget(btn, idx // GRID_COLS, idx % GRID_COLS)
        grid.setColumnStretch(GRID_COLS, 1)
        return grid

    def _make_button(self, char: str) -> QPushButton:
        btn = QPushButton(char)
        btn.setProperty("class", "EmojiButton")
        btn.setFixedSize(42, 40)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setToolTip(tr("emoji_tip", em=char))
        btn.clicked.connect(lambda checked=False, c=char: self._on_click(c))
        return btn

    def _on_click(self, char: str):
        settings.add_recent_emoji(char)
        self._build_recents()
        self.emoji_selected.emit(char)

    # ------------------------------------------------------------------
    def _build_recents(self):
        """(Re)construit la section « Récents » depuis les préférences."""
        while self.recents_layout.count():
            item = self.recents_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().hide()
                        sub.widget().deleteLater()

        recents = settings.get("recent_emojis", [])
        self.recents_container.setVisible(bool(recents))
        if not recents:
            return

        self.recents_layout.addWidget(self._make_header("cat_recent"))
        self.recents_layout.addLayout(self._make_grid(recents))

    # ------------------------------------------------------------------
    def apply_badge_colors(self, color: str):
        """Couleur des en-têtes de catégories selon le thème actif."""
        for label in self.findChildren(QLabel):
            if label.property("class") == "CategoryHeader":
                label.setStyleSheet(
                    f"color: {color}; font-size: 11.5px; font-weight: 700;"
                    " background: transparent; padding: 2px;"
                )
