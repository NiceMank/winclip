"""Gestionnaire d'icônes Microsoft Fluent Design haute résolution."""
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


def create_icon_pixmap(icon_name: str, size: int = 24, color: str = "#ffffff", bg_color: str = None) -> QPixmap:
    """Charge ou génère l'icône haute résolution avec antialiasing optimal."""
    png_path = ICONS_DIR / f"{icon_name}.png"

    if png_path.exists():
        src = QPixmap(str(png_path))
        if not src.isNull():
            # Mise à l'échelle douce haute fidélité
            target = src.scaled(
                size * 2, size * 2,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            target.setDevicePixelRatio(2.0)
            return target

    # Secours : Pixmap vide transparent
    empty = QPixmap(size, size)
    empty.fill(Qt.GlobalColor.transparent)
    return empty


def get_icon(icon_name: str, size: int = 20, color: str = "#ffffff", bg_color: str = None) -> QIcon:
    """Renvoie un QIcon haute définition prêt pour les boutons et menus."""
    pix = create_icon_pixmap(icon_name, size=size, color=color, bg_color=bg_color)
    return QIcon(pix)
