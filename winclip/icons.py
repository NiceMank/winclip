"""Gestionnaire d'icônes Microsoft Fluent Design haute résolution (avec cache).

Les icônes monochromes (close, pin) peuvent être teintées à la volée pour
rester lisibles quel que soit le thème actif (sombre ou clair).
"""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

# Icônes monochromes susceptibles d'être teintées selon le thème
TINTABLE_ICONS = {"close", "pin"}

# Cache des pixmaps déjà mis à l'échelle : (nom, taille, teinte) -> QPixmap
_PIXMAP_CACHE: dict[tuple[str, int, str | None], QPixmap] = {}


def tint_pixmap(pix: QPixmap, color: str) -> QPixmap:
    """Remplace la couleur d'un glyphe monochrome en préservant son alpha."""
    out = QPixmap(pix.size())
    out.setDevicePixelRatio(pix.devicePixelRatio())
    out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out)
    painter.drawPixmap(0, 0, pix)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(out.rect(), QColor(color))
    painter.end()
    return out


def create_icon_pixmap(icon_name: str, size: int = 24,
                       color: str | None = None, bg_color: str = None) -> QPixmap:
    """Charge l'icône PNG et la met à l'échelle en haute fidélité (DPR 2).

    `color` : teinte appliquée aux icônes monochromes (TINTABLE_ICONS).
    """
    tint = color if (color and icon_name in TINTABLE_ICONS) else None
    key = (icon_name, size, tint)
    cached = _PIXMAP_CACHE.get(key)
    if cached is not None:
        return cached

    png_path = ICONS_DIR / f"{icon_name}.png"
    target = None

    if png_path.exists():
        src = QPixmap(str(png_path))
        if not src.isNull():
            # Mise à l'échelle douce haute fidélité (x2 pour écrans HiDPI)
            target = src.scaled(
                size * 2, size * 2,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            target.setDevicePixelRatio(2.0)

    if target is None:
        # Secours : pixmap vide transparent
        target = QPixmap(size, size)
        target.fill(Qt.GlobalColor.transparent)

    if tint:
        target = tint_pixmap(target, tint)

    _PIXMAP_CACHE[key] = target
    return target


def get_icon(icon_name: str, size: int = 20,
             color: str | None = None, bg_color: str = None) -> QIcon:
    """Renvoie un QIcon haute définition prêt pour les boutons et menus."""
    return QIcon(create_icon_pixmap(icon_name, size=size, color=color, bg_color=bg_color))


def clear_cache() -> None:
    _PIXMAP_CACHE.clear()
