"""Configuration de WinClip Linux."""
import os
from pathlib import Path

# Répertoires utilisateurs
DATA_DIR = Path.home() / ".local" / "share" / "winclip"
DATA_DIR.mkdir(parents=True, exist_ok=True)

IMAGES_DIR = DATA_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "winclip.db"

# Socket UNIX pour la communication inter-processus (IPC)
UID = os.getuid()
SOCKET_PATH = f"/tmp/winclip_{UID}.sock"

# Paramètres généraux
MAX_HISTORY_ITEMS = 100
MAX_PREVIEW_LENGTH = 300
POPUP_WIDTH = 420
POPUP_HEIGHT = 580

# Couleurs du thème Windows 11 Fluent Dark
THEME = {
    "bg_main": "#1e1e1e",
    "bg_secondary": "#252525",
    "bg_card": "#2b2b2b",
    "bg_card_hover": "#363636",
    "bg_card_selected": "#3e3e3e",
    "bg_search": "#2a2a2a",
    "border": "#3a3a3a",
    "border_focus": "#0078d4",
    "accent": "#0078d4",
    "accent_hover": "#1084d8",
    "text_primary": "#f3f3f3",
    "text_secondary": "#aaaaaa",
    "text_muted": "#777777",
    "badge_pinned": "#f39c12",
    "badge_url": "#3498db",
    "badge_code": "#9b59b6",
    "badge_email": "#1abc9c",
    "badge_color": "#e67e22",
    "badge_image": "#e74c3c",
    "badge_text": "#95a5a6",
    "danger": "#e81123",
    "danger_hover": "#f1707a",
}
