"""Journalisation discrète des erreurs dans ~/.cache/winclip/winclip.log.

Le démon tourne en arrière-plan : plutôt que de perdre les exceptions,
on les horodate dans un fichier de log avec rotation simple (256 Ko max).
"""
import datetime
import os
import sys
import traceback

from .config import LOG_PATH

_MAX_LOG_BYTES = 256 * 1024


def log_message(message: str) -> None:
    """Ajoute une ligne horodatée au fichier de log (avec rotation)."""
    try:
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > _MAX_LOG_BYTES:
            # Rotation : on ne garde que la moitié la plus récente
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
            with open(LOG_PATH, "w", encoding="utf-8") as fh:
                fh.writelines(lines[len(lines) // 2:])
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] {message.rstrip()}\n")
    except OSError:
        pass


def log_exception(exc: BaseException | None = None) -> None:
    """Journalise une exception (par défaut l'exception courante)."""
    if exc is not None:
        text = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
    else:
        text = traceback.format_exc()
    if text and text.strip() != "NoneType: None":
        log_message(text)


def install_excepthook() -> None:
    """Capture les exceptions non gérées du démon dans le log."""
    def _hook(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        log_message("EXCEPTION NON GÉRÉE :\n" + text)
        # Comportement par défaut conservé (affichage stderr)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook
