#!/usr/bin/env python3
"""Rendu visuel hors-ligne de l'interface WinClip (captures PNG)."""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="winclip-visual-")
os.environ["XDG_DATA_HOME"] = os.path.join(_TMP, "data")
os.environ["XDG_CONFIG_HOME"] = os.path.join(_TMP, "config")
os.environ["XDG_CACHE_HOME"] = os.path.join(_TMP, "cache")
os.environ["XDG_RUNTIME_DIR"] = os.path.join(_TMP, "run")
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["LANG"] = "fr_FR.UTF-8"
os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/user/visual")
OUT.mkdir(parents=True, exist_ok=True)

from PyQt6.QtGui import QImage, QColor  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from winclip.app import WinClipApplication  # noqa: E402
from winclip.detector import detect_content_type  # noqa: E402
from winclip.settings import settings  # noqa: E402

settings.set("language", "fr")

app = WinClipApplication([])
win = app.window
db = app.db

# --- Jeu de données de démonstration ---
samples = [
    ("https://github.com/NiceMank/winclip",),
    ("def saluer(nom):\n    return f'Bonjour {nom} !'\n\nprint(saluer('WinClip'))",),
    ("#0078d4",),
    ("contact@winclip.app",),
    ("+33 6 12 34 56 78",),
    ("/home/niceman/Documents/rapport-2026.pdf",),
    ("SELECT id, nom FROM clients WHERE actif = 1 ORDER BY nom;",),
    ("Liste de courses :\n- pain\n- fromage\n- café",),
    ("Note rapide : penser à sauvegarder avant de fermer la session.",),
]
for (text,) in samples:
    ctype, meta = detect_content_type(text)
    db.add_clip(content=text, content_type=ctype, metadata=meta)

# Image de démonstration
img = QImage(320, 180, QImage.Format.Format_RGB32)
for y in range(180):
    for x in range(320):
        img.setPixel(x, y, QColor(int(40 + x * 0.5), int(90 + y * 0.4), 200).rgb())
from winclip.config import IMAGES_DIR
demo_path = IMAGES_DIR / "demo.png"
img.save(str(demo_path), "PNG")
db.add_clip(content=str(demo_path), content_type="image",
            metadata={"width": 320, "height": 180, "label": "Image · 320×180",
                      "label_key": "lbl_image", "label_args": {"w": 320, "h": 180}},
            thumbnail_path=str(demo_path))

# Épingler un élément
clips = db.get_clips()
db.toggle_pin(clips[1]["id"])

# Émojis récents
for em in ("🚀", "🔥", "😀"):
    settings.add_recent_emoji(em)

win.refresh_clips()
win.resize(420, 640)
win.show()
QApplication.processEvents()

# --- Capture thème sombre ---
pix = win.grab()
pix.save(str(OUT / "popup_dark.png"))
print("[✓] popup_dark.png")

# --- Capture thème clair ---
settings.set("theme", "light")
QApplication.processEvents()
pix = win.grab()
pix.save(str(OUT / "popup_light.png"))
print("[✓] popup_light.png")
settings.set("theme", "dark")
QApplication.processEvents()

# --- Onglet émojis ---
win._set_tab("emoji")
QApplication.processEvents()
pix = win.grab()
pix.save(str(OUT / "popup_emoji.png"))
print("[✓] popup_emoji.png")
win._set_tab("all")

# --- Fenêtre de paramètres ---
win.open_settings()
QApplication.processEvents()
dlg = win._settings_dialog
pix = dlg.grab()
pix.save(str(OUT / "settings.png"))
print("[✓] settings.png")

print("Rendus enregistrés dans", OUT)
