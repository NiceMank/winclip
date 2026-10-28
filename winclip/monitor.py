"""Surveillance continue du presse-papiers système (texte, images, fichiers).

Corrections & améliorations v2 :
  - hachage d'image compatible PyQt6 (QBuffer) — la v1 utilisait l'API
    PyQt5 `bits().asstring()` qui plantait silencieusement sous PyQt6 ;
  - protection des contenus sensibles (gestionnaires de mots de passe) ;
  - pause/reprise de la surveillance depuis les préférences ou le plateau ;
  - capture des fichiers copiés (text/uri-list) comme type "path" ;
  - redimensionnement des très grandes captures avant stockage.
"""
import hashlib
import time

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QIODevice, QBuffer, QUrl, Qt
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

from .config import IMAGES_DIR, SENSITIVE_MIME_MARKERS, MAX_IMAGE_DIMENSION, POLL_INTERVAL_MS
from .database import Database
from .detector import detect_content_type
from .settings import settings


def image_bytes_png(image: QImage) -> bytes:
    """Sérialise une QImage en PNG (compatible PyQt6, sans sip.voidptr)."""
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buf, "PNG")
    data = bytes(buf.data())
    buf.close()
    return data


def hash_image(image: QImage) -> str:
    """Empreinte stable et rapide d'une image (PNG d'une vignette 256 px)."""
    thumb = image
    if max(image.width(), image.height()) > 256:
        thumb = image.scaled(
            256, 256,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
    return hashlib.md5(image_bytes_png(thumb)).hexdigest()


class ClipboardMonitor(QObject):
    clip_added = pyqtSignal(int)     # id du clip nouvellement ajouté
    paused_changed = pyqtSignal(bool)

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.clipboard = QApplication.clipboard()
        self.last_text = ""
        self.last_image_hash = None
        self._is_internal_update = False

        # Événement natif Qt (X11 et Wayland avec KDE/GNOME récents)
        self.clipboard.dataChanged.connect(self._check_clipboard)

        # Filet de sécurité périodique pour garantir la détection sous Wayland
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._check_clipboard)
        self.poll_timer.start(POLL_INTERVAL_MS)

        # Mémoriser le contenu courant SANS l'enregistrer (pas d'inondation
        # de l'historique au démarrage du démon).
        self._init_current_content()

        # Réagir aux changements de préférences (pause, capture images…)
        settings.on_change(self._on_setting_changed)

    # ------------------------------------------------------------------
    def _init_current_content(self):
        try:
            text = self.clipboard.text()
            if text:
                self.last_text = text
            mime = self.clipboard.mimeData()
            if mime and mime.hasImage():
                image = self.clipboard.image()
                if not image.isNull():
                    self.last_image_hash = hash_image(image)
        except Exception:
            pass

    def _on_setting_changed(self, key: str, value):
        if key == "monitor_paused":
            self.paused_changed.emit(bool(value))

    # ------------------------------------------------------------------
    # Pause / reprise
    # ------------------------------------------------------------------
    def pause_monitoring(self):
        """Met en pause la détection pour éviter une boucle lors d'une copie interne."""
        self._is_internal_update = True

    def resume_monitoring(self):
        """Réactive la détection après une copie interne."""
        QTimer.singleShot(200, lambda: setattr(self, "_is_internal_update", False))

    @property
    def is_paused(self) -> bool:
        return bool(settings.get("monitor_paused", False))

    def set_paused(self, paused: bool):
        settings.set("monitor_paused", paused)
        if not paused:
            # À la reprise, réinitialiser l'état pour ne pas ré-enregistrer
            # en rafale le contenu courant… mais le capturer si nouveau.
            self._init_current_content()
        self.paused_changed.emit(paused)

    # ------------------------------------------------------------------
    # Détection de contenu sensible (mots de passe)
    # ------------------------------------------------------------------
    def _has_sensitive_marker(self) -> bool:
        if not settings.get("ignore_sensitive", True):
            return False
        try:
            mime = self.clipboard.mimeData()
            if mime is None:
                return False
            formats = [f.lower() for f in mime.formats()]
            return any(marker.lower() in formats for marker in SENSITIVE_MIME_MARKERS)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Boucle principale de vérification
    # ------------------------------------------------------------------
    def _check_clipboard(self):
        if self._is_internal_update or self.is_paused:
            return

        try:
            if self._has_sensitive_marker():
                # Contenu marqué sensible : on le mémorise (pour ne pas
                # retraiter) mais on ne l'enregistre JAMAIS.
                text = self.clipboard.text()
                if text:
                    self.last_text = text
                return

            # 1. Texte
            text = self.clipboard.text()
            if text and text != self.last_text:
                self.last_text = text
                self.last_image_hash = None
                content_type, metadata = detect_content_type(text)
                clip_id = self.db.add_clip(
                    content=text,
                    content_type=content_type,
                    metadata=metadata,
                )
                self.clip_added.emit(clip_id)
                return

            # 2. Fichiers copiés depuis un gestionnaire de fichiers
            mime = self.clipboard.mimeData()
            if mime and mime.hasUrls():
                local_paths = [
                    u.toLocalFile() for u in mime.urls()
                    if u.isLocalFile() and u.toLocalFile()
                ]
                if local_paths:
                    joined = "\n".join(local_paths)
                    if joined != self.last_text:
                        self.last_text = joined
                        content_type, metadata = detect_content_type(joined)
                        if content_type != "path":
                            content_type = "path"
                            metadata = {
                                "path": local_paths[0],
                                "paths": local_paths,
                                "label": f"{len(local_paths)} fichiers"
                                if len(local_paths) > 1 else "Chemin de fichier",
                                "label_key": "lbl_paths" if len(local_paths) > 1 else "lbl_path",
                                "label_args": {"n": len(local_paths)},
                            }
                        clip_id = self.db.add_clip(
                            content=joined,
                            content_type=content_type,
                            metadata=metadata,
                        )
                        self.clip_added.emit(clip_id)
                        return

            # 3. Images (captures d'écran, images copiées)
            if not settings.get("capture_images", True):
                return
            if mime and mime.hasImage():
                image = self.clipboard.image()
                if image.isNull():
                    return
                try:
                    img_hash = hash_image(image)
                except Exception:
                    return
                if img_hash == self.last_image_hash:
                    return
                self.last_image_hash = img_hash
                self._store_image(image)
        except Exception:
            # La surveillance ne doit jamais planter le démon
            from .logging_util import log_exception
            log_exception()

    # ------------------------------------------------------------------
    def _store_image(self, image: QImage):
        """Enregistre l'image (redimensionnée si gigantesque) et le clip."""
        # Respecter la taille maximale configurée (en mégaoctets, estimation brute)
        max_mb = int(settings.get("max_image_mb", 10))
        est_bytes = image.sizeInBytes()

        # Réduire les captures très grandes (> MAX_IMAGE_DIMENSION px)
        if max(image.width(), image.height()) > MAX_IMAGE_DIMENSION:
            image = image.scaled(
                MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        # Si l'image reste trop lourde, la convertir en JPEG qualité 85
        timestamp = int(time.time() * 1000)
        if est_bytes > max_mb * 1024 * 1024:
            img_path = IMAGES_DIR / f"clip_{timestamp}.jpg"
            saved = image.save(str(img_path), "JPEG", 85)
        else:
            img_path = IMAGES_DIR / f"clip_{timestamp}.png"
            saved = image.save(str(img_path), "PNG")

        if not saved:
            return

        metadata = {
            "width": image.width(),
            "height": image.height(),
            "label": f"Image ({image.width()}x{image.height()})",
            "label_key": "lbl_image",
            "label_args": {"w": image.width(), "h": image.height()},
        }
        clip_id = self.db.add_clip(
            content=str(img_path),
            content_type="image",
            metadata=metadata,
            thumbnail_path=str(img_path),
        )
        self.clip_added.emit(clip_id)
