#!/usr/bin/env python3
"""Suite de tests hors-ligne (QT_QPA_PLATFORM=offscreen) de WinClip.

Couvre : base de données, détection de contenu, préférences, i18n,
moniteur presse-papier (texte + image + suppression des fichiers),
interface (onglets, recherche, sélection clavier, thème) et IPC.

Usage :
    QT_QPA_PLATFORM=offscreen python3 tests/test_winclip.py
"""
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

# Environnement isolé AVANT tout import winclip (chemins XDG temporaires)
_TMP = tempfile.mkdtemp(prefix="winclip-tests-")
os.environ["XDG_DATA_HOME"] = os.path.join(_TMP, "data")
os.environ["XDG_CONFIG_HOME"] = os.path.join(_TMP, "config")
os.environ["XDG_CACHE_HOME"] = os.path.join(_TMP, "cache")
os.environ["XDG_RUNTIME_DIR"] = os.path.join(_TMP, "run")
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASSED = 0
FAILED = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [✓] {label}")
    else:
        FAILED += 1
        print(f"  [✗] {label} {detail}")


def section(title: str):
    print(f"\n=== {title} ===")


# ---------------------------------------------------------------------------
section("Modules fondamentaux")
from winclip import __version__
from winclip.config import IMAGES_DIR, get_palette
from winclip.database import Database, format_bytes
from winclip.detector import detect_content_type
from winclip.i18n import tr, set_language
from winclip.settings import settings

check("version 2.x", __version__.startswith("2."), __version__)

# --- Détection de contenu ---
set_language("fr")
cases = [
    ("https://github.com/NiceMank/winclip", "url"),
    ("www.example.org/page", "url"),
    ("contact@example.com", "email"),
    ("#0078d4", "color"),
    ("rgba(12, 34, 56, 0.5)", "color"),
    ("+33 6 12 34 56 78", "phone"),
    ("/home/user/documents/rapport.pdf", "path"),
    ('{"a": 1, "b": [2, 3]}', "code"),
    ("def bonjour(nom):\n    return f'Salut {nom}'", "code"),
    ("SELECT id FROM users WHERE active = 1", "code"),
    ("#!/bin/bash\necho 'hello'\n", "code"),
    ("Bonjour le monde", "text"),
    ("Ligne une\nLigne deux\nLigne trois", "text"),
]
for text, expected in cases:
    ctype, _meta = detect_content_type(text)
    check(f"détection {expected!r}", ctype == expected, f"→ {ctype}")

_lang_meta = detect_content_type("def bonjour(nom):\n    return f'Salut {nom}'")[1]
check("langage Python détecté", _lang_meta.get("label_args", {}).get("lang") == "Python",
      str(_lang_meta))
_sql_meta = detect_content_type("SELECT id, name FROM users WHERE active = 1")[1]
check("langage SQL détecté", _sql_meta.get("label_args", {}).get("lang") == "SQL",
      str(_sql_meta))

# --- i18n ---
check("tr FR", tr("title") == "Presse-papiers", tr("title"))
set_language("en")
check("tr EN", tr("title") == "Clipboard", tr("title"))
check("tr formatée", tr("lbl_url", domain="github.com") == "Link · github.com")
set_language("fr")
check("tr formatée FR", tr("lbl_url", domain="github.com") == "Lien · github.com")

# --- Base de données ---
db = Database()
cid = db.add_clip("texte de test", "text", {"label": "Texte court"})
check("ajout de clip", cid > 0)
cid2 = db.add_clip("https://example.com", "url", {"label": "Lien"})
db.toggle_pin(cid2)
clips = db.get_clips()
check("épinglé en premier", clips[0]["id"] == cid2)
found = db.get_clips(search="EXAMPLE")
check("recherche insensible casse", len(found) == 1, str(len(found)))
stats = db.count_clips()
check("comptage", stats["total"] == 2 and stats["pinned"] == 1, str(stats))
db.delete_clip(cid)
check("suppression", db.count_clips()["total"] == 1)
check("format_bytes", format_bytes(2048) == "2,0 Ko", format_bytes(2048))

# --- Préférences ---
settings.set("history_size", 9999)
check("validateur history_size (borne 1000)", settings.get("history_size") == 1000)
settings.set("theme", "nimportequoi")
check("validateur theme", settings.get("theme") == "dark")
settings.set("theme", "light")
check("persistance thème", settings.get("theme") == "light")
settings.load()
check("relecture fichier settings", settings.get("theme") == "light")
settings.set("theme", "dark")
settings.add_recent_emoji("🚀")
settings.add_recent_emoji("🔥")
settings.add_recent_emoji("🚀")
check("récents ordonnés & dédoublonnés",
      settings.get("recent_emojis") == ["🚀", "🔥"], str(settings.get("recent_emojis")))

# ---------------------------------------------------------------------------
section("Application complète (offscreen)")
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from winclip.app import WinClipApplication

app = WinClipApplication([])
win = app.window

check("fenêtre créée", win is not None)
# Historique non vide → pas de clip de bienvenue, mais drapeau posé
check("bienvenue gérée (historique non vide)", settings.get("welcomed") is True)

# Onglets
win._set_tab("pinned")
check("onglet épinglés", win.current_tab == "pinned" and win.stacked.currentIndex() == 0)
win._set_tab("emoji")
check("onglet émojis", win.stacked.currentIndex() == 1)
win._set_tab("all")

# Recherche dans l'interface
win.search_input.setText("example")
QTest.qWait(50)
check("filtrage recherche", len(win._cards) >= 1, str(len(win._cards)))
win.search_input.setText("zzzintrouvable")
QTest.qWait(50)
check("état vide recherche", len(win._cards) == 0)
win.search_input.clear()
QTest.qWait(50)

# Sélection clavier
total = len(win._cards)
if total >= 2:
    QTest.keyClick(win, Qt.Key.Key_Down)
    check("navigation ↓", win._selected_idx == 1, str(win._selected_idx))
    QTest.keyClick(win, Qt.Key.Key_Up)
    check("navigation ↑", win._selected_idx == 0, str(win._selected_idx))
    QTest.keyClick(win, Qt.Key.Key_End)
    check("navigation Fin", win._selected_idx == total - 1, str(win._selected_idx))
    QTest.keyClick(win, Qt.Key.Key_Home)
    check("navigation Début", win._selected_idx == 0, str(win._selected_idx))

# Moniteur : texte
before = db.count_clips()["total"]
QApplication.clipboard().setText("copié depuis le test " + str(time.time()))
win.monitor._check_clipboard()
check("moniteur capture le texte", db.count_clips()["total"] == before + 1)

# Moniteur : image (correctif PyQt6) + nettoyage du fichier à la suppression
img = QImage(120, 90, QImage.Format.Format_RGB32)
img.fill(QColor(200, 40, 40))
QApplication.clipboard().setImage(img)
win.monitor._check_clipboard()
img_clips = [c for c in db.get_clips(limit=500) if c["content_type"] == "image"]
check("moniteur capture l'image (hash PyQt6)", len(img_clips) >= 1)
if img_clips:
    path = img_clips[0]["content"]
    check("fichier image créé", os.path.isfile(path), path)
    db.delete_clip(img_clips[0]["id"])
    check("fichier image supprimé avec le clip", not os.path.exists(path))

# Pause du moniteur
win.monitor.set_paused(True)
paused_before = db.count_clips()["total"]
QApplication.clipboard().setText("pendant la pause " + str(time.time()))
win.monitor._check_clipboard()
check("pause respectée", db.count_clips()["total"] == paused_before)
win.monitor.set_paused(False)

# Contenu sensible ignoré
from PyQt6.QtCore import QMimeData
md = QMimeData()
md.setText("motdepasse123!")
md.setData("x-kde-passwordManagerHack", b"1")
QApplication.clipboard().setMimeData(md)
sens_before = db.count_clips()["total"]
win.monitor._check_clipboard()
check("contenu sensible ignoré", db.count_clips()["total"] == sens_before)

# Thème clair / sombre en direct
settings.set("theme", "light")
QTest.qWait(30)
palette = get_palette(settings.resolved_theme())
check("thème clair appliqué", palette["bg_main"] == "#f3f3f3")
settings.set("theme", "dark")
QTest.qWait(30)

# Fenêtre de paramètres
win.open_settings()
check("dialogue paramètres ouvert",
      win._settings_dialog is not None and win._settings_dialog.isVisible())
win._settings_dialog.refresh_stats()
win._settings_dialog.accept()

# Action copier-seulement (ne doit pas lever)
if win._cards:
    win._copy_only(win._clips[0])
    check("copier-seulement", not win.isVisible())

# ---------------------------------------------------------------------------
section("IPC (socket UNIX)")
result = {}


def ipc_client():
    import socket as _socket
    from winclip.config import SOCKET_PATH
    try:
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(SOCKET_PATH)
        s.sendall(b"ping")
        result["resp"] = s.recv(64).decode().strip()
        s.close()
    except Exception as exc:  # noqa: BLE001
        result["resp"] = f"erreur: {exc}"


thread = threading.Thread(target=ipc_client)
thread.start()
deadline = time.time() + 3
while thread.is_alive() and time.time() < deadline:
    QApplication.processEvents()
    time.sleep(0.02)
thread.join(timeout=2)
check("IPC ping → pong", result.get("resp") == "pong", str(result.get("resp")))

result.clear()


def run_status():
    from winclip.app import send_ipc_command
    import socket as _socket
    from winclip.config import SOCKET_PATH
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect(SOCKET_PATH)
    s.sendall(b"status")
    result["resp"] = s.recv(256).decode().strip()
    s.close()


thread = threading.Thread(target=run_status)
thread.start()
deadline = time.time() + 3
while thread.is_alive() and time.time() < deadline:
    QApplication.processEvents()
    time.sleep(0.02)
thread.join(timeout=2)
check("IPC status", str(result.get("resp", "")).startswith("ok:"), str(result.get("resp")))

# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print(f"RÉSULTAT : {PASSED} réussis, {FAILED} échoués")
shutil.rmtree(_TMP, ignore_errors=True)
sys.exit(1 if FAILED else 0)
