"""Widget représentant une carte d'élément copié dans le presse-papier."""
import time
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QColor, QCursor
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget
)

from ..config import THEME, MAX_PREVIEW_LENGTH
from ..icons import get_icon, create_icon_pixmap


def format_relative_time(timestamp: float) -> str:
    """Renvoie une chaîne conviviale du temps écoulé."""
    diff = time.time() - timestamp
    if diff < 60:
        return "À l'instant"
    elif diff < 3600:
        mins = int(diff / 60)
        return f"Il y a {mins} min"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"Il y a {hours} h"
    else:
        days = int(diff / 86400)
        return f"Il y a {days} j"


class ClipItemWidget(QFrame):
    clicked = pyqtSignal(dict)
    pin_toggled = pyqtSignal(int)
    deleted = pyqtSignal(int)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.setProperty("class", "ClipCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 1. En-tête de la carte (Icône de type + Libellé + Heure + Actions)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        # Icône du type
        content_type = self.item.get("content_type", "text")
        type_icon_map = {
            "url": ("url", THEME["badge_url"]),
            "code": ("code", THEME["badge_code"]),
            "email": ("email", THEME["badge_email"]),
            "color": ("color", THEME["badge_color"]),
            "image": ("image", THEME["badge_image"]),
            "text": ("text", THEME["badge_text"]),
        }
        icon_name, icon_color = type_icon_map.get(content_type, ("text", THEME["badge_text"]))

        icon_label = QLabel()
        icon_pixmap = create_icon_pixmap(icon_name, size=20)
        icon_label.setPixmap(icon_pixmap)
        header_layout.addWidget(icon_label)

        # Libellé du type
        metadata = self.item.get("metadata", {})
        label_text = metadata.get("label", content_type.capitalize())
        type_badge = QLabel(label_text)
        type_badge.setProperty("class", "TypeBadge")
        header_layout.addWidget(type_badge)

        # Temps relatif
        header_layout.addStretch()
        time_text = format_relative_time(self.item.get("updated_at", time.time()))
        time_label = QLabel(time_text)
        time_label.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 11px;")
        header_layout.addWidget(time_label)

        # Bouton Épingler
        is_pinned = bool(self.item.get("is_pinned", 0))
        self.pin_btn = QPushButton()
        self.pin_btn.setProperty("class", "CardActionBtn")
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_pin_icon(is_pinned)
        self.pin_btn.clicked.connect(self._on_pin_clicked)
        header_layout.addWidget(self.pin_btn)

        # Bouton Supprimer
        delete_btn = QPushButton()
        delete_btn.setProperty("class", "CardActionBtn")
        delete_btn.setFixedSize(26, 26)
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setIcon(get_icon("trash", size=16))
        delete_btn.clicked.connect(self._on_delete_clicked)
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # 2. Corps de la carte selon le type
        body_widget = self._create_body_widget()
        layout.addWidget(body_widget)

    def _create_body_widget(self) -> QWidget:
        content_type = self.item.get("content_type", "text")
        content = self.item.get("content", "")

        # A. Cas Image
        if content_type == "image":
            img_path = self.item.get("thumbnail_path") or content
            container = QWidget()
            img_layout = QHBoxLayout(container)
            img_layout.setContentsMargins(0, 4, 0, 4)

            pix = QPixmap(str(img_path))
            if not pix.isNull():
                thumb_label = QLabel()
                scaled_pix = pix.scaled(
                    240, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                thumb_label.setPixmap(scaled_pix)
                thumb_label.setStyleSheet("border-radius: 6px; border: 1px solid #444;")
                img_layout.addWidget(thumb_label)
                img_layout.addStretch()
                return container

        # B. Cas Couleur
        if content_type == "color":
            container = QWidget()
            c_layout = QHBoxLayout(container)
            c_layout.setContentsMargins(0, 2, 0, 2)
            c_layout.setSpacing(10)

            color_box = QLabel()
            color_box.setFixedSize(28, 28)
            color_val = self.item.get("metadata", {}).get("color", content)
            color_box.setStyleSheet(f"background-color: {color_val}; border-radius: 6px; border: 1px solid #666;")
            c_layout.addWidget(color_box)

            color_label = QLabel(content)
            color_label.setStyleSheet(f"color: {THEME['text_primary']}; font-weight: 600; font-size: 14px;")
            c_layout.addWidget(color_label)
            c_layout.addStretch()
            return container

        # C. Cas Code
        if content_type == "code":
            lines = content.splitlines()
            preview_lines = lines[:4]
            preview = "\n".join(preview_lines)
            if len(lines) > 4:
                preview += "\n..."

            code_label = QLabel(preview)
            code_label.setProperty("class", "CodeText")
            code_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            code_label.setWordWrap(True)
            return code_label

        # D. Cas URL
        if content_type == "url":
            url_label = QLabel(content)
            url_label.setStyleSheet(f"color: {THEME['badge_url']}; font-size: 13px; text-decoration: underline;")
            url_label.setWordWrap(True)
            return url_label

        # E. Cas Texte standard
        preview = content
        if len(preview) > MAX_PREVIEW_LENGTH:
            preview = preview[:MAX_PREVIEW_LENGTH] + "..."

        text_label = QLabel(preview)
        text_label.setProperty("class", "ContentText")
        text_label.setWordWrap(True)
        return text_label

    def _update_pin_icon(self, is_pinned: bool):
        if is_pinned:
            self.pin_btn.setIcon(get_icon("pin_filled", size=16))
            self.pin_btn.setToolTip("Désépingler")
        else:
            self.pin_btn.setIcon(get_icon("pin", size=16))
            self.pin_btn.setToolTip("Épingler")

    def _on_pin_clicked(self):
        clip_id = self.item["id"]
        self.pin_toggled.emit(clip_id)

    def _on_delete_clicked(self):
        clip_id = self.item["id"]
        self.deleted.emit(clip_id)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Ne pas déclencher si on a cliqué sur un bouton d'action
            if not self.pin_btn.underMouse():
                self.clicked.emit(self.item)
        super().mousePressEvent(event)
