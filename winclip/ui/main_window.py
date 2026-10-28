"""Fenêtre popup principale du presse-papier façon Windows 11 Fluent UI."""
import time
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize, QTimer
from PyQt6.QtGui import QKeyEvent, QGuiApplication, QCursor, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QStackedWidget, QFrame,
    QButtonGroup, QGraphicsDropShadowEffect
)

from ..config import POPUP_WIDTH, POPUP_HEIGHT, THEME
from ..database import Database
from ..icons import get_icon, create_icon_pixmap
from ..paster import get_active_window_id, paste_clipboard_to_window, paste_text_to_window
from .clip_item import ClipItemWidget
from .emoji_picker import EmojiPickerWidget
from .styles import MAIN_STYLESHEET


class DraggableHeader(QFrame):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.main_win.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self.main_win.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    item_pasted = pyqtSignal(dict)

    def __init__(self, db: Database, monitor=None):
        super().__init__()
        self.db = db
        self.monitor = monitor
        self.current_tab = "all"  # 'all', 'pinned', 'emoji'
        self.search_text = ""

        self._setup_window_properties()
        self._init_ui()
        self.refresh_clips()

    def _setup_window_properties(self):
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(POPUP_WIDTH, POPUP_HEIGHT)
        self._can_auto_hide = False

    def _init_ui(self):
        # Widget central avec marges pour l'ombre
        outer_widget = QWidget()
        outer_layout = QVBoxLayout(outer_widget)
        outer_layout.setContentsMargins(12, 12, 12, 12)

        # Conteneur principal arrondi
        self.main_container = QFrame()
        self.main_container.setObjectName("MainContainer")
        self.main_container.setStyleSheet(MAIN_STYLESHEET)

        # Ombre portée moderne
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.main_container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 8)
        container_layout.setSpacing(0)

        # 1. En-tête
        header = self._create_header()
        container_layout.addWidget(header)

        # 2. Barre d'onglets (Presse-papier / Épinglés / Émojis)
        tabs_bar = self._create_tabs_bar()
        container_layout.addWidget(tabs_bar)

        # 3. Barre de recherche
        self.search_container = self._create_search_bar()
        container_layout.addWidget(self.search_container)

        # 4. Zone empilée (Liste des clips / Sélecteur émojis)
        self.stacked = QStackedWidget()

        # Page 0 : Liste des clips
        self.clips_scroll = QScrollArea()
        self.clips_scroll.setWidgetResizable(True)
        self.clips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.clips_content = QWidget()
        self.clips_layout = QVBoxLayout(self.clips_content)
        self.clips_layout.setContentsMargins(8, 4, 8, 4)
        self.clips_layout.setSpacing(4)
        self.clips_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.clips_scroll.setWidget(self.clips_content)

        self.stacked.addWidget(self.clips_scroll)

        # Page 1 : Sélecteur d'émojis
        self.emoji_picker = EmojiPickerWidget()
        self.emoji_picker.emoji_selected.connect(self._on_emoji_selected)
        self.stacked.addWidget(self.emoji_picker)

        container_layout.addWidget(self.stacked, 1)

        outer_layout.addWidget(self.main_container)
        self.setCentralWidget(outer_widget)

    def _create_header(self) -> QWidget:
        header = DraggableHeader(self)
        header.setObjectName("HeaderBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Icône titre Fluent
        icon_label = QLabel()
        icon_label.setPixmap(create_icon_pixmap("clipboard", size=22))
        layout.addWidget(icon_label)

        # Titre
        title_label = QLabel("Presse-papiers")
        title_label.setObjectName("HeaderTitle")
        layout.addWidget(title_label)

        layout.addStretch()

        # Bouton Effacer tout
        self.clear_btn = QPushButton()
        self.clear_btn.setObjectName("ClearButton")
        self.clear_btn.setToolTip("Effacer tout l'historique non-épinglé")
        self.clear_btn.setIcon(get_icon("clear", size=18))
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.clicked.connect(self._on_clear_all)
        layout.addWidget(self.clear_btn)

        # Bouton Fermer
        close_btn = QPushButton()
        close_btn.setObjectName("CloseButton")
        close_btn.setToolTip("Fermer (Échap)")
        close_btn.setIcon(get_icon("close", size=14))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

        return header

    def _create_tabs_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 4)
        layout.setSpacing(6)

        self.tab_group = QButtonGroup(self)

        self.tab_all = QPushButton("  Presse-papiers")
        self.tab_all.setProperty("class", "TabButton")
        self.tab_all.setIcon(get_icon("clipboard", size=18))
        self.tab_all.setCheckable(True)
        self.tab_all.setChecked(True)
        self.tab_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_all.clicked.connect(lambda: self._set_tab("all"))
        self.tab_group.addButton(self.tab_all)
        layout.addWidget(self.tab_all)

        self.tab_pinned = QPushButton("  Épinglés")
        self.tab_pinned.setProperty("class", "TabButton")
        self.tab_pinned.setIcon(get_icon("pin_filled", size=18))
        self.tab_pinned.setCheckable(True)
        self.tab_pinned.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_pinned.clicked.connect(lambda: self._set_tab("pinned"))
        self.tab_group.addButton(self.tab_pinned)
        layout.addWidget(self.tab_pinned)

        self.tab_emoji = QPushButton("  Émojis & Icônes")
        self.tab_emoji.setProperty("class", "TabButton")
        self.tab_emoji.setIcon(get_icon("emoji", size=18))
        self.tab_emoji.setCheckable(True)
        self.tab_emoji.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_emoji.clicked.connect(lambda: self._set_tab("emoji"))
        self.tab_group.addButton(self.tab_emoji)
        layout.addWidget(self.tab_emoji)

        layout.addStretch()
        return bar

    def _create_search_bar(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 6, 12, 6)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Rechercher dans l'historique...")
        self.search_input.addAction(get_icon("search", size=16), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        return container

    def _set_tab(self, tab_name: str):
        self.current_tab = tab_name
        if tab_name == "emoji":
            self.search_container.hide()
            self.clear_btn.hide()
            self.stacked.setCurrentIndex(1)
        else:
            self.search_container.show()
            self.clear_btn.show()
            self.stacked.setCurrentIndex(0)
            self.refresh_clips()

    def _on_search_changed(self, text: str):
        self.search_text = text.strip()
        self.refresh_clips()

    def refresh_clips(self):
        """Recharge et affiche les éléments filtrés."""
        # Vider la liste actuelle
        while self.clips_layout.count() > 0:
            item = self.clips_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        only_pinned = (self.current_tab == "pinned")
        clips = self.db.get_clips(search=self.search_text, only_pinned=only_pinned)

        if not clips:
            empty_widget = self._create_empty_state(only_pinned)
            self.clips_layout.addWidget(empty_widget)
            return

        for clip in clips:
            card = ClipItemWidget(clip)
            card.clicked.connect(self._on_item_clicked)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.deleted.connect(self._on_item_deleted)
            self.clips_layout.addWidget(card)

    def _create_empty_state(self, only_pinned: bool) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 60, 20, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_label = QLabel()
        icon_name = "pin_filled" if only_pinned else "clipboard"
        icon_label.setPixmap(create_icon_pixmap(icon_name, size=64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        msg = "Aucun élément épinglé" if only_pinned else "L'historique est vide"
        sub = "Épinglez des éléments avec 📌 pour les conserver ici" if only_pinned else "Les éléments que vous copiez (Ctrl+C) apparaîtront ici."

        lbl_msg = QLabel(msg)
        lbl_msg.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 15px; font-weight: 600;")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_msg)

        lbl_sub = QLabel(sub)
        lbl_sub.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 12px;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_sub)

        return container

    def _on_item_clicked(self, item: dict):
        """Place l'élément dans le presse-papier, ferme la fenêtre et colle automatiquement."""
        if self.monitor:
            self.monitor.pause_monitoring()

        cb = QGuiApplication.clipboard()
        content_type = item.get("content_type", "text")
        content = item.get("content", "")

        if content_type == "image":
            from PyQt6.QtGui import QImage
            img = QImage(content)
            if not img.isNull():
                cb.setImage(img)
        else:
            cb.setText(content)

        if self.monitor:
            self.monitor.resume_monitoring()

        target_wid = getattr(self, "target_window_id", None)
        self.hide()
        self.item_pasted.emit(item)

        # Coller automatiquement dans l'application après restauration du focus
        QTimer.singleShot(90, lambda: paste_clipboard_to_window(target_wid))

    def _on_emoji_selected(self, char: str):
        """Copie et colle directement l'émoji/icône sans fermer la fenêtre (permet les clics multiples)."""
        if self.monitor:
            self.monitor.pause_monitoring()

        cb = QGuiApplication.clipboard()
        cb.setText(char)

        if self.monitor:
            self.monitor.resume_monitoring()

        target_wid = getattr(self, "target_window_id", None)

        # Coller directement l'émoji dans la fenêtre cible
        paste_text_to_window(target_wid, char)

        # Note: La fenêtre RESTE OUVERTE pour permettre à l'utilisateur de cliquer
        # plusieurs fois d'affilée sur les icônes/émojis !
        # Elle sera fermée uniquement si l'utilisateur clique en dehors ou appuie sur Échap.

    def _on_pin_toggled(self, clip_id: int):
        self.db.toggle_pin(clip_id)
        self.refresh_clips()

    def _on_item_deleted(self, clip_id: int):
        self.db.delete_clip(clip_id)
        self.refresh_clips()

    def _on_clear_all(self):
        self.db.clear_all(keep_pinned=True)
        self.refresh_clips()

    def show_near_cursor(self):
        """Affiche la fenêtre popup exactement au niveau du curseur de la souris."""
        # Enregistrer l'ID de la fenêtre active précédente avant de s'afficher
        prev_wid = get_active_window_id()
        if prev_wid and prev_wid != str(self.winId()):
            self.target_window_id = prev_wid

        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        # Placer le coin supérieur gauche près de la pointe du curseur
        x = cursor_pos.x() + 4
        y = cursor_pos.y() + 4

        # Si la fenêtre dépasse à droite, l'ouvrir vers la gauche du curseur
        if x + self.width() > screen_geo.right():
            x = cursor_pos.x() - self.width() - 4

        # Si la fenêtre dépasse en bas, l'ouvrir au-dessus du curseur
        if y + self.height() > screen_geo.bottom():
            y = cursor_pos.y() - self.height() - 4

        # Garder à l'intérieur de l'écran
        x = max(screen_geo.left() + 4, min(x, screen_geo.right() - self.width() - 4))
        y = max(screen_geo.top() + 4, min(y, screen_geo.bottom() - self.height() - 4))

        self.move(x, y)
        self.refresh_clips()
        self._can_auto_hide = False
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus()
        self.search_input.selectAll()
        # N'autoriser la fermeture automatique sur perte de focus qu'après stabilisation
        QTimer.singleShot(600, lambda: setattr(self, "_can_auto_hide", True))

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_near_cursor()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_is_dragging", False) and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def changeEvent(self, event):
        # Fermer automatiquement si la fenêtre perd le focus (comme Windows), mais seulement après stabilisation
        if event.type() == event.Type.ActivationChange:
            if getattr(self, "_can_auto_hide", False) and not self.isActiveWindow():
                self.hide()
        super().changeEvent(event)
