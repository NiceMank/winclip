"""Widget représentant une carte d'élément copié dans le presse-papier.

Design v2 façon Windows 11 :
  - bande latérale ambre pour les éléments épinglés ;
  - état « sélectionné » (navigation clavier) avec liseré accent ;
  - menu contextuel (coller / copier / épingler / ouvrir / supprimer) ;
  - vignettes d'images aux coins arrondis ;
  - libellés de type traduits (FR/EN).
"""
import time
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPoint, QSize
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QCursor
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)

from ..config import MAX_PREVIEW_LENGTH
from ..i18n import tr
from ..icons import get_icon, create_icon_pixmap

# Icône et couleur d'accent par type de contenu
TYPE_ICON_MAP = {
    "url":   ("url", "badge_url"),
    "code":  ("code", "badge_code"),
    "email": ("email", "badge_email"),
    "color": ("color", "badge_color"),
    "image": ("image", "badge_image"),
    "path":  ("folder", "badge_path"),
    "phone": ("phone", "badge_phone"),
    "text":  ("text", "badge_text"),
}


def format_relative_time(timestamp: float) -> str:
    """Renvoie une chaîne conviviale du temps écoulé (traduite)."""
    diff = time.time() - timestamp
    if diff < 60:
        return tr("time_now")
    elif diff < 3600:
        return tr("time_min", n=int(diff / 60))
    elif diff < 86400:
        return tr("time_hour", n=int(diff / 3600))
    else:
        return tr("time_day", n=int(diff / 86400))


def resolve_label(item: dict) -> str:
    """Construit le libellé de type : clé i18n prioritaire, repli v1."""
    metadata = item.get("metadata", {})
    key = metadata.get("label_key")
    if key:
        args = metadata.get("label_args") or {}
        return tr(key, **args)
    if metadata.get("label"):
        return metadata["label"]
    return tr(f"type_{item.get('content_type', 'text')}")


def _font_px(family: str, px: int, mono: bool = False):
    """Fabrique une QFont alignée sur les tailles déclarées dans le QSS."""
    from PyQt6.QtGui import QFont
    f = QFont(family)
    f.setPixelSize(px)
    if mono:
        f.setStyleHint(QFont.StyleHint.Monospace)
    return f


def elide_lines(text: str, font, max_px: int = 320) -> str:
    """Coupe chaque ligne avec « … » pour tenir dans `max_px` pixels.

    Empêche tout token trop long d'élargir la carte au-delà du popup.
    """
    from PyQt6.QtGui import QFontMetrics
    fm = QFontMetrics(font)
    out = []
    for line in text.splitlines():
        if fm.horizontalAdvance(line) > max_px:
            line = fm.elidedText(line, Qt.TextElideMode.ElideRight, max_px)
        out.append(line)
    return "\n".join(out)


def elide_chars(text: str, max_chars: int) -> str:
    """Coupe chaque ligne à `max_chars` caractères (déterministe, sans fonte).

    Convertit les tabulations en espaces (expandtabs) pour éviter que Qt
    n'élargisse démesurément la carte lors du calcul de taille.
    """
    out = []
    for line in text.splitlines():
        line = line.expandtabs(4)
        if len(line) > max_chars:
            line = line[: max_chars - 1].rstrip() + "…"
        out.append(line)
    return "\n".join(out)


def rounded_pixmap(pix: QPixmap, max_w: int, max_h: int, radius: int = 6) -> QPixmap:
    """Vignette aux coins arrondis, rendue en 2x pour les écrans HiDPI."""
    dpr = 2.0
    scaled = pix.scaled(
        int(max_w * dpr), int(max_h * dpr),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    out = QPixmap(scaled.size())
    out.setDevicePixelRatio(dpr)
    out.fill(Qt.GlobalColor.transparent)

    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    logical = QRectF(0, 0, scaled.width() / dpr, scaled.height() / dpr)
    path = QPainterPath()
    path.addRoundedRect(logical, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(logical.toRect(), scaled)
    painter.end()
    return out


class ClipItemWidget(QFrame):
    clicked = pyqtSignal(dict)                 # clic gauche → coller/copier
    copy_requested = pyqtSignal(dict)          # clic molette → copier seulement
    pin_toggled = pyqtSignal(int)
    deleted = pyqtSignal(int)
    open_requested = pyqtSignal(dict)          # ouvrir URL / chemin
    context_requested = pyqtSignal(dict, QPoint)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self._palette = None
        self.setProperty("class", "ClipCard")
        self.setProperty("pinned", bool(item.get("is_pinned", 0)))
        self.setProperty("selected", False)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._init_ui()

    def minimumSizeHint(self) -> QSize:
        sh = super().minimumSizeHint()
        return QSize(0, sh.height())

    def apply_theme_colors(self, palette: dict):
        """(Ré)applique les couleurs du thème actif (badge + icône épingler)."""
        self._palette = palette
        badge_color = palette.get(self._badge_color_key, palette["badge_text"])
        self.set_badge_color(badge_color)
        content_type = self.item.get("content_type", "text")
        icon_name, _ = TYPE_ICON_MAP.get(content_type, ("text", "badge_text"))
        if hasattr(self, "type_icon_label"):
            self.type_icon_label.setPixmap(create_icon_pixmap(icon_name, size=16, color=badge_color))
        self._update_pin_icon(bool(self.item.get("is_pinned", 0)))
        if hasattr(self, "delete_btn"):
            self.delete_btn.setIcon(get_icon("trash", size=14, color=palette["text_muted"]))

    # ------------------------------------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 8)
        layout.setSpacing(5)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        # Icône du type de contenu
        content_type = self.item.get("content_type", "text")
        icon_name, badge_color_key = TYPE_ICON_MAP.get(
            content_type, ("text", "badge_text")
        )
        self.type_icon_label = QLabel()
        self.type_icon_label.setPixmap(create_icon_pixmap(icon_name, size=16))
        self.type_icon_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(self.type_icon_label)

        # Libellé du type (badge coloré — couleur appliquée par le thème)
        type_badge = QLabel(resolve_label(self.item))
        type_badge.setProperty("class", "TypeBadge")
        type_badge.setStyleSheet("background: transparent;")
        header_layout.addWidget(type_badge)
        self._badge_color_key = badge_color_key

        header_layout.addStretch()

        # Temps relatif
        time_label = QLabel(format_relative_time(self.item.get("updated_at", time.time())))
        time_label.setProperty("class", "TimeLabel")
        header_layout.addWidget(time_label)

        # Bouton Épingler
        self.pin_btn = QPushButton()
        self.pin_btn.setProperty("class", "CardActionBtn")
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_pin_icon(bool(self.item.get("is_pinned", 0)))
        self.pin_btn.clicked.connect(self._on_pin_clicked)
        header_layout.addWidget(self.pin_btn)

        # Bouton Supprimer
        self.delete_btn = QPushButton()
        self.delete_btn.setProperty("class", "CardActionBtn")
        self.delete_btn.setObjectName("DeleteCardBtn")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setToolTip(tr("act_delete"))
        self.delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_btn.setIcon(get_icon("trash", size=14))
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        header_layout.addWidget(self.delete_btn)

        layout.addLayout(header_layout)
        layout.addWidget(self._create_body_widget())

    # ------------------------------------------------------------------
    def set_badge_color(self, color: str):
        """Applique la couleur d'accent du badge selon le thème actif."""
        badge = self.findChild(QLabel, None)
        for child in self.findChildren(QLabel):
            if child.property("class") == "TypeBadge":
                child.setStyleSheet(f"color: {color}; background: transparent;")
                break

    # ------------------------------------------------------------------
    def _create_body_widget(self) -> QWidget:
        content_type = self.item.get("content_type", "text")
        content = self.item.get("content", "")
        metadata = self.item.get("metadata", {})

        # A. Image → vignette arrondie
        if content_type == "image":
            img_path = self.item.get("thumbnail_path") or content
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            img_layout = QHBoxLayout(container)
            img_layout.setContentsMargins(0, 2, 0, 0)

            pix = QPixmap(str(img_path))
            if not pix.isNull():
                thumb_label = QLabel()
                thumb_label.setProperty("class", "ImageThumb")
                thumb_label.setPixmap(rounded_pixmap(pix, 260, 120, radius=6))
                img_layout.addWidget(thumb_label)
            else:
                missing = QLabel(tr("type_image") + " — ⚠")
                missing.setProperty("class", "ContentText")
                img_layout.addWidget(missing)
            img_layout.addStretch()
            return container

        # B. Couleur → pastille + valeur
        if content_type == "color":
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            c_layout = QHBoxLayout(container)
            c_layout.setContentsMargins(0, 2, 0, 0)
            c_layout.setSpacing(10)

            color_val = metadata.get("color", content)
            swatch = QLabel()
            swatch.setFixedSize(30, 30)
            swatch.setStyleSheet(
                f"background-color: {color_val}; border-radius: 7px;"
                " border: 1px solid rgba(128,128,128,0.5);"
            )
            c_layout.addWidget(swatch)

            color_label = QLabel(content)
            color_label.setProperty("class", "ColorValue")
            c_layout.addWidget(color_label)
            c_layout.addStretch()
            return container

        # C. Code → bloc monospace (4 lignes max, lignes coupées à la largeur)
        if content_type == "code":
            lines = content.splitlines()
            preview = "\n".join(lines[:4])
            if len(lines) > 4:
                preview += "\n…"
            code_label = QLabel()
            code_label.setProperty("class", "CodeText")
            code_label.setText(elide_chars(preview, 36))
            code_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            code_label.setWordWrap(False)
            code_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            return code_label

        # D. URL → lien souligné
        if content_type == "url":
            url_label = QLabel()
            url_label.setProperty("class", "UrlText")
            url_label.setText(elide_chars(content, 42))
            url_label.setStyleSheet("text-decoration: underline;")
            url_label.setWordWrap(True)
            url_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            url_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            return url_label

        # E. Chemin de fichier → monospace abrégé (~) et coupé
        if content_type == "path":
            paths = metadata.get("paths") or [metadata.get("path", content)]
            display = "\n".join(
                str(Path(p)).replace(str(Path.home()), "~", 1) for p in paths[:3]
            )
            if len(paths) > 3:
                display += f"\n… (+{len(paths) - 3})"
            path_label = QLabel()
            path_label.setProperty("class", "PathText")
            path_label.setText(elide_chars(display, 36))
            path_label.setWordWrap(True)
            path_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            return path_label

        # F. Téléphone
        if content_type == "phone":
            phone_label = QLabel(content)
            phone_label.setProperty("class", "PhoneText")
            phone_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            return phone_label

        # G. E-mail
        if content_type == "email":
            email_label = QLabel(content)
            email_label.setProperty("class", "ContentText")
            email_label.setWordWrap(True)
            email_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            return email_label

        # H. Texte standard → aperçu 3 lignes, tokens trop longs coupés
        preview = content
        if len(preview) > MAX_PREVIEW_LENGTH:
            preview = preview[:MAX_PREVIEW_LENGTH].rsplit("\n", 1)[0] + "…"
        lines = preview.splitlines()
        if len(lines) > 3:
            preview = "\n".join(lines[:3]) + "…"

        text_label = QLabel()
        text_label.setProperty("class", "ContentText")
        text_font = _font_px('DejaVu Sans', 13)
        text_label.setText(elide_lines(preview, text_font, 300))
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        text_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        return text_label

    # ------------------------------------------------------------------
    # État de sélection (navigation clavier)
    # ------------------------------------------------------------------
    def set_selected(self, selected: bool):
        if self.property("selected") == selected:
            return
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    # ------------------------------------------------------------------
    def _update_pin_icon(self, is_pinned: bool):
        tint = (self._palette or {}).get("text_secondary")
        if is_pinned:
            self.pin_btn.setIcon(get_icon("pin_filled", size=14))
            self.pin_btn.setToolTip(tr("act_unpin"))
        else:
            self.pin_btn.setIcon(get_icon("pin", size=14, color=tint))
            self.pin_btn.setToolTip(tr("act_pin"))

    def _on_pin_clicked(self):
        self.pin_toggled.emit(self.item["id"])

    def _on_delete_clicked(self):
        self.deleted.emit(self.item["id"])

    # ------------------------------------------------------------------
    # Souris
    # ------------------------------------------------------------------
    def _is_action_button(self, pos) -> bool:
        child = self.childAt(pos)
        return isinstance(child, QPushButton)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if self._is_action_button(pos):
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.copy_requested.emit(self.item)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_requested.emit(self.item, event.globalPosition().toPoint())
        super().mousePressEvent(event)
