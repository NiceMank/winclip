"""Préférences utilisateur persistantes de WinClip (JSON, écriture atomique).

Emplacement : ~/.config/winclip/settings.json
Le singleton `settings` est importé par tous les modules.
"""
import json
import locale
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from .config import SETTINGS_PATH

# Valeurs par défaut — toute nouvelle clé est fusionnée à la lecture,
# si bien qu'un ancien fichier settings.json reste compatible.
DEFAULTS: dict[str, Any] = {
    # Apparence
    "language": "auto",            # "auto" | "fr" | "en"
    "theme": "dark",               # "dark" | "light" | "auto"
    "show_hints": True,            # barre d'état avec raccourcis clavier
    # Comportement
    "auto_paste": True,            # coller automatiquement après un clic
    "emoji_action": "insert",      # "insert" (frappe directe) | "copy"
    "ignore_sensitive": True,      # ignorer les mots de passe (KeePassXC…)
    # Historique
    "history_size": 100,           # 25…1000 éléments
    "capture_images": True,        # enregistrer les images copiées
    "max_image_mb": 10,            # taille max d'une image enregistrée
    # État
    "monitor_paused": False,       # surveillance en pause
    "recent_emojis": [],           # derniers émojis utilisés
    "welcomed": False,             # message de bienvenue déjà ajouté
}

_VALIDATORS = {
    "language": lambda v: v if v in ("auto", "fr", "en") else "auto",
    "theme": lambda v: v if v in ("dark", "light", "auto") else "dark",
    "history_size": lambda v: max(25, min(1000, int(v))),
    "max_image_mb": lambda v: max(1, min(100, int(v))),
    "emoji_action": lambda v: v if v in ("insert", "copy") else "insert",
}


class Settings:
    """Préférences avec notification des changements (pattern observateur)."""

    def __init__(self, path: Path = SETTINGS_PATH):
        self.path = Path(path)
        self._data: dict[str, Any] = dict(DEFAULTS)
        self._listeners: list[Callable[[str, Any], None]] = []
        self.load()

    # ------------------------------------------------------------------ I/O
    def load(self) -> None:
        """Charge le fichier JSON et le fusionne avec les valeurs par défaut."""
        self._data = dict(DEFAULTS)
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                if isinstance(stored, dict):
                    for key, value in stored.items():
                        if key in DEFAULTS:
                            self._data[key] = self._validate(key, value)
        except (json.JSONDecodeError, OSError, ValueError, TypeError):
            pass  # fichier corrompu → on repart des valeurs par défaut

    def save(self) -> None:
        """Écriture atomique : fichier temporaire puis remplacement."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                dir=str(self.path.parent), prefix=".settings-", suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self.path)
        except OSError:
            try:
                os.unlink(tmp_name)
            except Exception:
                pass

    # ------------------------------------------------------------- accès
    @staticmethod
    def _validate(key: str, value: Any) -> Any:
        validator = _VALIDATORS.get(key)
        if validator:
            try:
                return validator(value)
            except (ValueError, TypeError):
                return DEFAULTS.get(key)
        if isinstance(DEFAULTS.get(key), bool):
            return bool(value)
        if isinstance(DEFAULTS.get(key), list):
            return list(value) if isinstance(value, list) else []
        return value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any, save: bool = True) -> None:
        value = self._validate(key, value)
        if self._data.get(key) == value:
            return
        self._data[key] = value
        if save:
            self.save()
        for listener in list(self._listeners):
            try:
                listener(key, value)
            except Exception:
                pass

    def as_dict(self) -> dict:
        return dict(self._data)

    # ------------------------------------------------- résolution dynamique
    def resolved_language(self) -> str:
        """Résout 'auto' en fonction de la locale système (fr sinon en)."""
        lang = self.get("language", "auto")
        if lang != "auto":
            return lang
        try:
            loc = locale.getlocale()[0] or os.environ.get("LANG", "")
        except Exception:
            loc = os.environ.get("LANG", "")
        return "fr" if str(loc).lower().startswith("fr") else "en"

    def resolved_theme(self) -> str:
        """Résout 'auto' via l'indice de schéma de couleurs de Qt (>= 6.5)."""
        theme = self.get("theme", "dark")
        if theme != "auto":
            return theme
        try:
            from PyQt6.QtGui import QGuiApplication
            from PyQt6.QtCore import Qt
            app = QGuiApplication.instance()
            if app is not None:
                scheme = app.styleHints().colorScheme()
                if scheme == Qt.ColorScheme.Light:
                    return "light"
        except Exception:
            pass
        return "dark"

    # --------------------------------------------------------- observateur
    def on_change(self, callback: Callable[[str, Any], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, Any], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    # ------------------------------------------------------------- émojis
    def add_recent_emoji(self, char: str, cap: int = 24) -> None:
        recents = [c for c in self.get("recent_emojis", []) if c != char]
        recents.insert(0, char)
        self.set("recent_emojis", recents[:cap])


# Singleton partagé par toute l'application
settings = Settings()
