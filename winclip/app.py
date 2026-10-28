"""Point d'entrée principal : démon, serveur IPC, plateau système et CLI.

Commandes (winclip <commande>) :
  toggle     ouvre/ferme le panneau (défaut)
  show       ouvre le panneau près du curseur
  hide       ferme le panneau
  clear      vide l'historique non épinglé
  clear-all  vide TOUT l'historique (épinglés inclus)
  status     état du démon + statistiques
  quit       quitte le démon
  daemon     démarre le démon en avant-plan (pour systemd)

Si aucune instance ne tourne, `winclip`/`toggle`/`show` démarre le démon
en tâche de fond détachée puis lui transmet la commande.
"""
import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from . import __version__
from .config import SOCKET_PATH, DATA_DIR
from .database import Database
from .i18n import tr, set_language
from .icons import get_icon
from .logging_util import install_excepthook, log_message
from .monitor import ClipboardMonitor
from .settings import settings
from .ui.main_window import MainWindow

MAIN_PY = Path(__file__).resolve().parent.parent / "main.py"
CONTROL_COMMANDS = ("toggle", "show", "hide", "clear", "clear-all", "quit", "ping", "status")


# ---------------------------------------------------------------------------
# IPC client
# ---------------------------------------------------------------------------
def send_ipc_command(command: str, expect_response: bool = False,
                     timeout: float = 0.6) -> str | None:
    """Envoie une commande à l'instance active via socket UNIX.

    Renvoie la réponse texte si `expect_response`, True/None sinon
    (None = aucune instance à l'écoute).
    """
    if not os.path.exists(SOCKET_PATH):
        return None
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(SOCKET_PATH)
        sock.sendall(command.encode("utf-8"))
        if expect_response:
            try:
                data = sock.recv(4096).decode("utf-8", errors="replace").strip()
            except socket.timeout:
                data = ""
            sock.close()
            return data or None
        sock.close()
        return "ok"
    except OSError:
        return None


def wait_for_daemon(deadline_s: float = 3.0) -> bool:
    """Attend que le socket IPC réponde à 'ping'."""
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        if send_ipc_command("ping", expect_response=True, timeout=0.3) == "pong":
            return True
        time.sleep(0.1)
    return False


def spawn_daemon() -> bool:
    """Démarre un démon détaché (indépendant du terminal appelant)."""
    try:
        env = dict(os.environ)
        env.setdefault("QT_QPA_PLATFORM", "xcb")
        env["PYTHONPATH"] = str(MAIN_PY.parent) + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
        subprocess.Popen(
            [sys.executable, str(MAIN_PY), "daemon"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
            cwd=str(MAIN_PY.parent),
        )
        return wait_for_daemon()
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class WinClipApplication(QObject):
    def __init__(self, sys_argv):
        super().__init__()
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
        self.app = QApplication(sys_argv)
        self.app.setApplicationName("WinClip")
        self.app.setApplicationVersion(__version__)
        self.app.setQuitOnLastWindowClosed(False)

        # Langue résolue AVANT la construction de l'interface
        set_language(settings.resolved_language())

        # Icône globale
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        self.app_icon = (
            QIcon(str(icon_path)) if icon_path.exists()
            else get_icon("clipboard", size=32)
        )
        self.app.setWindowIcon(self.app_icon)

        # 1. Base de données
        self.db = Database()

        # 2. Surveillance du presse-papier
        self.monitor = ClipboardMonitor(self.db)

        # 3. Fenêtre principale (applique aussi la feuille de style globale)
        self.window = MainWindow(self.db, self.monitor)
        self.monitor.clip_added.connect(
            lambda _id: self.window.isVisible() and self.window.refresh_clips()
        )
        self.window.item_copied.connect(self._on_item_copied)

        # 4. Message de bienvenue au tout premier lancement
        self._add_welcome_clip()

        # 5. Serveur IPC pour les raccourcis système (Super+V)
        self._init_ipc_server()

        # 6. Icône dans la barre système (systray)
        self._init_systray()

    # ------------------------------------------------------------------
    def _add_welcome_clip(self):
        if settings.get("welcomed", False):
            return
        settings.set("welcomed", True)
        if self.db.count_clips()["total"] == 0:
            from .detector import detect_content_type
            text = tr("welcome_text")
            content_type, metadata = detect_content_type(text)
            self.db.add_clip(content=text, content_type="text", metadata=metadata)

    # ------------------------------------------------------------------
    # Serveur IPC
    # ------------------------------------------------------------------
    def _init_ipc_server(self):
        QLocalServer.removeServer(SOCKET_PATH)
        self.server = QLocalServer(self.app)
        self.server.newConnection.connect(self._handle_client_connection)
        if not self.server.listen(SOCKET_PATH):
            log_message(f"IPC: impossible d'écouter sur {SOCKET_PATH}")

    def _handle_client_connection(self):
        client = self.server.nextPendingConnection()
        if not client:
            return

        def read_data():
            cmd = bytes(client.readAll()).decode("utf-8", errors="replace").strip()
            response = self._process_command(cmd)
            if response is not None:
                client.write(response.encode("utf-8"))
                client.flush()
                client.waitForBytesWritten(300)
            client.disconnectFromServer()

        client.readyRead.connect(read_data)

    def _process_command(self, cmd: str) -> str | None:
        """Exécute une commande IPC et renvoie la réponse texte."""
        if cmd == "toggle":
            self.window.toggle_visibility()
            return "ok"
        if cmd == "show":
            self.window.show_near_cursor()
            return "ok"
        if cmd == "hide":
            self.window.hide()
            return "ok"
        if cmd == "clear":
            self.db.clear_all(keep_pinned=True)
            self.window.refresh_clips()
            return "ok"
        if cmd == "clear-all":
            self.db.clear_all(keep_pinned=False)
            self.window.refresh_clips()
            return "ok"
        if cmd == "ping":
            return "pong"
        if cmd == "status":
            stats = self.db.count_clips()
            paused = "paused" if settings.get("monitor_paused", False) else "active"
            return f"ok:{stats['total']}:{stats['pinned']}:{paused}"
        if cmd == "quit":
            self.app.quit()
            return "ok"
        return None

    # ------------------------------------------------------------------
    # Plateau système (systray)
    # ------------------------------------------------------------------
    def _init_systray(self):
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray = QSystemTrayIcon(self.app_icon, self.app)
        self.tray.setToolTip(tr("app_tooltip"))

        menu = QMenu()

        act_open = menu.addAction(get_icon("clipboard", size=15), tr("tray_open"))
        act_open.triggered.connect(self.window.show_near_cursor)

        act_pinned = menu.addAction(get_icon("pin_filled", size=15), tr("tray_pinned"))
        act_pinned.triggered.connect(
            lambda: (self.window._set_tab("pinned"), self.window.show_near_cursor())
        )

        act_emoji = menu.addAction(get_icon("emoji", size=15), tr("tray_emoji"))
        act_emoji.triggered.connect(
            lambda: (self.window._set_tab("emoji"), self.window.show_near_cursor())
        )

        menu.addSeparator()

        act_settings = menu.addAction(get_icon("settings", size=15), tr("tray_settings"))
        act_settings.triggered.connect(self._open_settings_from_tray)

        self.act_pause = menu.addAction(get_icon("pause", size=15), tr("tray_pause"))
        self.act_pause.setCheckable(True)
        self.act_pause.setChecked(bool(settings.get("monitor_paused", False)))
        self.act_pause.toggled.connect(self._on_tray_pause_toggled)
        self.monitor.paused_changed.connect(self._on_monitor_paused_changed)

        act_clear = menu.addAction(get_icon("clear", size=15), tr("tray_clear"))
        act_clear.triggered.connect(self._on_tray_clear)

        menu.addSeparator()

        from .config import get_palette
        _pal = get_palette(settings.resolved_theme())
        act_quit = menu.addAction(
            get_icon("close", size=15, color=_pal["text_secondary"]), tr("tray_quit")
        )
        act_quit.triggered.connect(self.app.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _open_settings_from_tray(self):
        self.window.open_settings()

    def _on_tray_pause_toggled(self, checked: bool):
        self.monitor.set_paused(checked)
        if self.tray:
            self.tray.showMessage(
                "WinClip",
                tr("tray_paused_body") if checked else tr("tray_resumed_body"),
                self.app_icon, 2000,
            )

    def _on_monitor_paused_changed(self, paused: bool):
        if hasattr(self, "act_pause"):
            self.act_pause.blockSignals(True)
            self.act_pause.setChecked(paused)
            self.act_pause.setIcon(get_icon("play" if paused else "pause", size=15))
            self.act_pause.setText(tr("tray_resume") if paused else tr("tray_pause"))
            self.act_pause.blockSignals(False)

    def _on_tray_clear(self):
        self.db.clear_all(keep_pinned=True)
        self.window.refresh_clips()

    def _on_item_copied(self, _item: dict):
        if self.tray:
            self.tray.showMessage(
                tr("tray_copied_title"), tr("tray_copied_body"), self.app_icon, 1600
            )

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.window.toggle_visibility()

    # ------------------------------------------------------------------
    def run(self):
        return self.app.exec()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_status():
    """Affiche l'état du démon (IPC si vivant, base locale sinon)."""
    resp = send_ipc_command("status", expect_response=True)
    if resp and resp.startswith("ok:"):
        try:
            _, total, pinned, state = resp.split(":")
            state_txt = "en pause ⏸" if state == "paused" else "actif 🟢"
            print(f"WinClip {__version__} — démon {state_txt}")
            print(f"  Éléments : {total} (épinglés : {pinned})")
            print(f"  Données  : {DATA_DIR}")
            return 0
        except ValueError:
            pass
    # Démon absent : lire la base directement
    try:
        db = Database()
        stats = db.count_clips()
        print(f"WinClip {__version__} — démon arrêté 🔴")
        print(f"  Éléments : {stats['total']} (épinglés : {stats['pinned']})")
        print(f"  Données  : {DATA_DIR}")
    except Exception as exc:
        print(f"WinClip {__version__} — démon arrêté 🔴 ({exc})")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="winclip",
        description="WinClip — gestionnaire de presse-papier façon Windows 11 pour Linux.",
        epilog=(
            "Exemples :\n"
            "  winclip            ouvre le panneau (démarre le démon si besoin)\n"
            "  winclip status     état du démon et statistiques\n"
            "  winclip clear      vide l'historique non épinglé\n"
            "  winclip daemon     démarre le démon en avant-plan (systemd)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command", nargs="?", default="toggle",
        choices=[*CONTROL_COMMANDS, "daemon"],
        help="commande à exécuter (défaut : toggle)",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="équivalent à 'winclip daemon' (compatibilité v1)",
    )
    parser.add_argument(
        "--version", action="version", version=f"WinClip {__version__}",
    )
    return parser


def main():
    install_excepthook()
    parser = build_parser()
    args = parser.parse_args()

    command = "daemon" if args.daemon else args.command
    if command == "ping":
        command = "status"

    # --- Mode démon : avant-plan, pas de fenêtre spontanée ---
    if command == "daemon":
        app = WinClipApplication(sys.argv)
        log_message(f"démarrage du démon WinClip {__version__} (pid {os.getpid()})")
        sys.exit(app.run())

    # --- Commandes de contrôle : IPC vers l'instance existante ---
    if command == "status":
        sys.exit(_print_status())

    sent = send_ipc_command(command)
    if sent is not None:
        sys.exit(0)

    # Aucune instance à l'écoute :
    #  - toggle/show → démarrer le démon détaché puis rejouer la commande ;
    #  - hide/clear/… → rien à faire, sortie propre.
    if command in ("toggle", "show"):
        if spawn_daemon():
            send_ipc_command(command)
            sys.exit(0)
    elif command in ("hide", "clear", "clear-all", "quit"):
        sys.exit(0)

    # Ultime repli : daemon intégré en avant-plan (ex. lancement direct .desktop)
    app = WinClipApplication(sys.argv)
    if command in ("toggle", "show"):
        app.window.show_near_cursor()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
