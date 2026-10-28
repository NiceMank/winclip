"""Configuration de WinClip Linux — chemins XDG, palettes de thèmes et constantes.

Tous les chemins suivent la spécification XDG Base Directory :
  - Config  : ~/.config/winclip/
  - Données : ~/.local/share/winclip/
  - Cache   : ~/.cache/winclip/
  - Socket  : $XDG_RUNTIME_DIR/winclip-<uid>.sock (sécurisé, non devinable)
"""
import os
from pathlib import Path

APP_NAME = "WinClip"
APP_ID = "winclip"


def _xdg_dir(env_var: str, fallback: Path) -> Path:
    """Renvoie le répertoire XDG demandé (ou son repli standard)."""
    val = os.environ.get(env_var, "").strip()
    if val:
        return Path(val).expanduser()
    return fallback


HOME = Path.home()

XDG_CONFIG_HOME = _xdg_dir("XDG_CONFIG_HOME", HOME / ".config")
XDG_DATA_HOME = _xdg_dir("XDG_DATA_HOME", HOME / ".local" / "share")
XDG_CACHE_HOME = _xdg_dir("XDG_CACHE_HOME", HOME / ".cache")
XDG_RUNTIME_DIR = _xdg_dir("XDG_RUNTIME_DIR", Path("/tmp"))

CONFIG_DIR = XDG_CONFIG_HOME / APP_ID
DATA_DIR = XDG_DATA_HOME / APP_ID
CACHE_DIR = XDG_CACHE_HOME / APP_ID
IMAGES_DIR = DATA_DIR / "images"

for _d in (CONFIG_DIR, DATA_DIR, CACHE_DIR, IMAGES_DIR):
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

DB_PATH = DATA_DIR / "winclip.db"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
LOG_PATH = CACHE_DIR / "winclip.log"

# Socket UNIX pour la communication inter-processus (IPC).
# Placé dans XDG_RUNTIME_DIR (0700) plutôt que /tmp : seul l'utilisateur
# peut s'y connecter — pas d'usurpation possible par un autre compte local.
UID = os.getuid()
SOCKET_PATH = str(XDG_RUNTIME_DIR / f"{APP_ID}-{UID}.sock")

# ---------------------------------------------------------------------------
# Paramètres généraux (valeurs par défaut ; surchargeables via les préférences)
# ---------------------------------------------------------------------------
MAX_HISTORY_ITEMS = 100          # défaut si settings indisponibles
HISTORY_MIN = 25
HISTORY_MAX = 1000
MAX_PREVIEW_LENGTH = 300         # caractères affichés dans une carte
MAX_IMAGE_DIMENSION = 2560       # px : les captures plus grandes sont réduites
POLL_INTERVAL_MS = 500           # filet de sécurité sous Wayland

POPUP_WIDTH = 420
POPUP_HEIGHT = 600

# Marques MIME utilisées par les gestionnaires de mots de passe pour signaler
# un contenu sensible (KeePassXC, Klipper, Bitwarden, 1Password, etc.).
SENSITIVE_MIME_MARKERS = (
    "x-kde-passwordManagerHack",
    "application/x-ninja-password",
    "x-special/ninja-clipboard",
    "password",
    "secret",
)

# ---------------------------------------------------------------------------
# Palettes — Thème sombre « Fluent Dark » (Windows 11)
# ---------------------------------------------------------------------------
DARK_PALETTE = {
    "bg_main": "#202020",
    "bg_secondary": "#272727",
    "bg_card": "#2b2b2b",
    "bg_card_hover": "#323232",
    "bg_card_selected": "#383838",
    "bg_search": "#2a2a2a",
    "bg_input": "#1c1c1c",
    "bg_code": "#181818",
    "border": "#3a3a3a",
    "border_subtle": "#2f2f2f",
    "border_focus": "#4cc2ff",
    "accent": "#0078d4",
    "accent_hover": "#1a86d9",
    "accent_light": "#4cc2ff",
    "text_primary": "#ffffff",
    "text_secondary": "#b3b3b3",
    "text_muted": "#7a7a7a",
    "badge_pinned": "#f39c12",
    "badge_url": "#3498db",
    "badge_code": "#9b59b6",
    "badge_email": "#1abc9c",
    "badge_color": "#e67e22",
    "badge_image": "#e74c3c",
    "badge_text": "#95a5a6",
    "badge_path": "#d4a017",
    "badge_phone": "#2ecc71",
    "danger": "#e81123",
    "danger_hover": "#f1707a",
    "success": "#6ccb5f",
    "warning": "#fce100",
    "scroll_handle": "#555555",
    "scroll_handle_hover": "#777777",
    "shadow_alpha": 190,
}

# ---------------------------------------------------------------------------
# Palettes — Thème clair « Fluent Light » (Windows 11)
# ---------------------------------------------------------------------------
LIGHT_PALETTE = {
    "bg_main": "#f3f3f3",
    "bg_secondary": "#fbfbfb",
    "bg_card": "#ffffff",
    "bg_card_hover": "#f6f6f6",
    "bg_card_selected": "#e8e8e8",
    "bg_search": "#ffffff",
    "bg_input": "#ffffff",
    "bg_code": "#f8f8f8",
    "border": "#d9d9d9",
    "border_subtle": "#e8e8e8",
    "border_focus": "#0067c0",
    "accent": "#0067c0",
    "accent_hover": "#1975c5",
    "accent_light": "#005fb8",
    "text_primary": "#1a1a1a",
    "text_secondary": "#5c5c5c",
    "text_muted": "#8a8a8a",
    "badge_pinned": "#b26a00",
    "badge_url": "#0f6cbd",
    "badge_code": "#8764b8",
    "badge_email": "#0e7a63",
    "badge_color": "#ca5010",
    "badge_image": "#c50f1f",
    "badge_text": "#69797e",
    "badge_path": "#9d730b",
    "badge_phone": "#107c10",
    "danger": "#c42b1c",
    "danger_hover": "#d13438",
    "success": "#107c10",
    "warning": "#9d5d00",
    "scroll_handle": "#c8c8c8",
    "scroll_handle_hover": "#a8a8a8",
    "shadow_alpha": 90,
}

PALETTES = {"dark": DARK_PALETTE, "light": LIGHT_PALETTE}

# Compatibilité ascendante : THEME pointe vers la palette sombre par défaut.
# Le code récent doit utiliser get_palette() (thème dynamique).
THEME = DARK_PALETTE


def get_palette(theme_name: str = "dark") -> dict:
    """Renvoie la palette correspondant au thème demandé ('dark' ou 'light')."""
    return PALETTES.get(theme_name, DARK_PALETTE)
