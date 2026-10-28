"""Surveillance continue du presse-papier système (texte et images)."""
import hashlib
import time
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QClipboard, QImage
from PyQt6.QtWidgets import QApplication

from .config import IMAGES_DIR
from .database import Database
from .detector import detect_content_type


class ClipboardMonitor(QObject):
    clip_added = pyqtSignal(int)  # Émet l'id du clip nouvellement ajouté

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.clipboard = QApplication.clipboard()
        self.last_text = ""
        self.last_image_hash = None
        self._is_internal_update = False

        # Connexion à l'événement Qt
        self.clipboard.dataChanged.connect(self._check_clipboard)

        # Timer de secours périodique (500ms) pour garantir la détection sous Wayland
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._check_clipboard)
        self.poll_timer.start(500)

        # Initialisation de la valeur actuelle
        self._init_current_content()

    def _init_current_content(self):
        text = self.clipboard.text()
        if text:
            self.last_text = text

    def pause_monitoring(self):
        """Met en pause la détection pour éviter une boucle lors d'une copie interne."""
        self._is_internal_update = True

    def resume_monitoring(self):
        """Réactive la détection."""
        # Un léger délai permet à l'événement de se propager
        QTimer.singleShot(200, lambda: setattr(self, "_is_internal_update", False))

    def _check_clipboard(self):
        if self._is_internal_update:
            return

        # 1. Vérification du texte
        text = self.clipboard.text()
        if text and text != self.last_text:
            self.last_text = text
            content_type, metadata = detect_content_type(text)
            clip_id = self.db.add_clip(
                content=text,
                content_type=content_type,
                metadata=metadata
            )
            self.clip_added.emit(clip_id)
            return

        # 2. Vérification des images (captures d'écran / copier image)
        mime = self.clipboard.mimeData()
        if mime and mime.hasImage():
            image = self.clipboard.image()
            if not image.isNull():
                img_data = image.bits().asstring(image.sizeInBytes())
                img_hash = hashlib.md5(img_data).hexdigest()
                if img_hash != self.last_image_hash:
                    self.last_image_hash = img_hash
                    # Sauvegarde locale de l'image
                    timestamp = int(time.time() * 1000)
                    img_path = IMAGES_DIR / f"clip_{timestamp}.png"
                    image.save(str(img_path), "PNG")

                    metadata = {
                        "width": image.width(),
                        "height": image.height(),
                        "label": f"Image ({image.width()}x{image.height()})"
                    }

                    clip_id = self.db.add_clip(
                        content=str(img_path),
                        content_type="image",
                        metadata=metadata,
                        thumbnail_path=str(img_path)
                    )
                    self.clip_added.emit(clip_id)
