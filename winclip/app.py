"""Point d'entrée principal avec serveur IPC et gestion d'instance unique."""
import os
import sys
import socket
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from .config import SOCKET_PATH, THEME
from .database import Database
from .icons import get_icon, create_icon_pixmap
from .monitor import ClipboardMonitor
from .ui.main_window import MainWindow


def send_ipc_command(command: str) -> bool:
    """Tente d'envoyer une commande à une instance existante via socket UNIX en 1ms."""
    if not os.path.exists(SOCKET_PATH):
        return False
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect(SOCKET_PATH)
        sock.sendall(command.encode("utf-8"))
        sock.close()
        return True
    except Exception:
        return False


class WinClipApplication:
    def __init__(self, sys_argv):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
        self.app = QApplication(sys_argv)
        self.app.setApplicationName("WinClip")
        self.app.setQuitOnLastWindowClosed(False)

        # Icône globale
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
        else:
            app_icon = get_icon("clipboard", size=32, color=THEME["accent"])
        self.app.setWindowIcon(app_icon)

        # 1. Base de données
        self.db = Database()

        # 2. Surveillance du presse-papier
        self.monitor = ClipboardMonitor(self.db)

        # 3. Fenêtre principale
        self.window = MainWindow(self.db, self.monitor)
        self.monitor.clip_added.connect(lambda _: self.window.refresh_clips())

        # 4. Serveur IPC pour les raccourcis système (Win+V)
        self._init_ipc_server()

        # 5. Icône dans la barre système (Systray)
        self._init_systray(app_icon)

    def _init_ipc_server(self):
        # Nettoyer l'ancien socket s'il existe
        QLocalServer.removeServer(SOCKET_PATH)

        self.server = QLocalServer(self.app)
        self.server.newConnection.connect(self._handle_client_connection)
        self.server.listen(SOCKET_PATH)

    def _handle_client_connection(self):
        client = self.server.nextPendingConnection()
        if not client:
            return

        def read_data():
            cmd = bytes(client.readAll()).decode("utf-8").strip()
            if cmd == "toggle":
                self.window.toggle_visibility()
            elif cmd == "show":
                self.window.show_near_cursor()
            elif cmd == "hide":
                self.window.hide()
            elif cmd == "quit":
                self.app.quit()
            client.disconnectFromServer()

        client.readyRead.connect(read_data)

    def _init_systray(self, icon: QIcon):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray = QSystemTrayIcon(icon, self.app)
        self.tray.setToolTip("WinClip — Presse-papier moderne")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #444;
                color: #fff;
                padding: 4px;
                border-radius: 6px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 4px 0;
            }
        """)

        act_open = menu.addAction(get_icon("clipboard", size=16, color="#ffffff"), "Presse-papier (Win+V)")
        act_open.triggered.connect(self.window.show_near_cursor)

        act_pinned = menu.addAction(get_icon("pin_filled", size=16, color=THEME["badge_pinned"]), "Éléments épinglés")
        act_pinned.triggered.connect(lambda: (self.window._set_tab("pinned"), self.window.show_near_cursor()))

        act_emoji = menu.addAction(get_icon("emoji", size=16, color=THEME["badge_color"]), "Émojis & Symboles")
        act_emoji.triggered.connect(lambda: (self.window._set_tab("emoji"), self.window.show_near_cursor()))

        menu.addSeparator()

        act_clear = menu.addAction(get_icon("clear", size=16, color=THEME["text_secondary"]), "Vider l'historique")
        act_clear.triggered.connect(self.window._on_clear_all)

        menu.addSeparator()

        act_quit = menu.addAction("Quitter WinClip")
        act_quit.triggered.connect(self.app.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.window.toggle_visibility()

    def run(self):
        return self.app.exec()


def main():
    args = sys.argv[1:]

    # Si un argument comme 'toggle', 'show' ou 'hide' est passé, tenter l'IPC d'abord
    command = "toggle"
    if args:
        command = args[0].replace("--", "")

    # Tentative d'envoi à l'instance active
    if send_ipc_command(command):
        sys.exit(0)

    # Si aucun serveur n'écoute, lancer le daemon
    app = WinClipApplication(sys.argv)

    # Si demandé via la commande, afficher la fenêtre directement
    if command in ("toggle", "show"):
        app.window.show_near_cursor()

    sys.exit(app.run())


if __name__ == "__main__":
    main()
