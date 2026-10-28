"""Fenêtre popup principale du presse-papier façon Windows 11 Fluent UI.

Nouveautés v2 :
  - navigation clavier complète (↑↓, ⏎, Ctrl+C, Suppr, Ctrl+P, Ctrl+,) ;
  - menu contextuel sur chaque carte ;
  - thème sombre/clair dynamique appliqué en direct ;
  - barre d'état (nombre d'éléments, état de la surveillance, astuces) ;
  - fondu à l'ouverture, bouton paramètres et pause dans l'en-tête ;
  - interface traduite FR/EN.
"""
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QUrl,
)
from PyQt6.QtGui import QKeyEvent, QGuiApplication, QCursor, QColor, QImage, QDesktopServices
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QStackedWidget, QFrame,
    QButtonGroup, QGraphicsDropShadowEffect, QMenu, QApplication,
)

from ..config import POPUP_WIDTH, POPUP_HEIGHT, get_palette
from ..database import Database
from ..i18n import tr
from ..icons import get_icon, create_icon_pixmap
from ..paster import get_active_window_id, paste_clipboard_to_window, paste_text_to_window
from ..settings import settings
from .clip_item import ClipItemWidget
from .emoji_picker import EmojiPickerWidget
from .settings_dialog import SettingsDialog
from .styles import build_stylesheet


class DraggableHeader(QFrame):
    """En-tête permettant de déplacer la fenêtre sans bordure."""

    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = (
                event.globalPosition().toPoint()
                - self.main_win.frameGeometry().topLeft()
            )
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
    item_copied = pyqtSignal(dict)

    def __init__(self, db: Database, monitor=None):
        super().__init__()
        self.db = db
        self.monitor = monitor
        self.current_tab = "all"   # 'all' | 'pinned' | 'emoji'
        self.search_text = ""
        self._cards: list[ClipItemWidget] = []
        self._clips: list[dict] = []
        self._selected_idx = -1
        self._settings_dialog: SettingsDialog | None = None
        self.target_window_id = None

        self._setup_window_properties()
        self._init_ui()
        self.apply_theme()
        settings.on_change(self._on_setting_changed)
        self.refresh_clips()

    # ------------------------------------------------------------------
    # Fenêtre
    # ------------------------------------------------------------------
    def _setup_window_properties(self):
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(POPUP_WIDTH, POPUP_HEIGHT)
        self._can_auto_hide = False

    def _init_ui(self):
        outer_widget = QWidget()
        outer_layout = QVBoxLayout(outer_widget)
        outer_layout.setContentsMargins(12, 12, 12, 12)

        self.main_container = QFrame()
        self.main_container.setObjectName("MainContainer")

        # Ombre portée moderne
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(28)
        self._shadow.setColor(QColor(0, 0, 0, 180))
        self._shadow.setOffset(0, 8)
        self.main_container.setGraphicsEffect(self._shadow)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addWidget(self._create_header())
        container_layout.addWidget(self._create_tabs_bar())

        self.search_container = self._create_search_bar()
        container_layout.addWidget(self.search_container)

        # Zone empilée : liste des clips / sélecteur d'émojis
        self.stacked = QStackedWidget()

        self.clips_scroll = QScrollArea()
        self.clips_scroll.setWidgetResizable(True)
        self.clips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.clips_content = QWidget()
        self.clips_content.setStyleSheet("background: transparent;")
        self.clips_layout = QVBoxLayout(self.clips_content)
        self.clips_layout.setContentsMargins(10, 6, 4, 6)
        self.clips_layout.setSpacing(5)
        self.clips_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.clips_scroll.setWidget(self.clips_content)
        self.stacked.addWidget(self.clips_scroll)

        self.emoji_picker = EmojiPickerWidget()
        self.emoji_picker.emoji_selected.connect(self._on_emoji_selected)
        self.stacked.addWidget(self.emoji_picker)

        container_layout.addWidget(self.stacked, 1)

        # Barre d'état (pied de fenêtre)
        self.footer = self._create_footer()
        container_layout.addWidget(self.footer)

        outer_layout.addWidget(self.main_container)
        self.setCentralWidget(outer_widget)

    # ------------------------------------------------------------------
    def _header_button(self, object_name: str, icon_name: str, tooltip_key: str,
                       size: int = 15) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName(object_name)
        btn.setProperty("class", "IconButton")
        btn.setToolTip(tr(tooltip_key))
        btn.setIcon(get_icon(icon_name, size=size))
        btn.setFixedSize(28, 28)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        return btn

    def _create_header(self) -> QWidget:
        header = DraggableHeader(self)
        header.setObjectName("HeaderBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(create_icon_pixmap("clipboard", size=20))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        self.title_label = QLabel(tr("title"))
        self.title_label.setObjectName("HeaderTitle")
        layout.addWidget(self.title_label)
        layout.addStretch()

        # Bouton Pause / Reprendre la surveillance
        self.pause_btn = self._header_button("PauseButton", "pause", "tip_pause", size=14)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        layout.addWidget(self.pause_btn)

        # Bouton Paramètres
        self.settings_btn = self._header_button("SettingsButton2", "settings", "tip_settings", size=15)
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)

        # Bouton Effacer l'historique
        self.clear_btn = self._header_button("ClearButton", "clear", "tip_clear", size=16)
        self.clear_btn.clicked.connect(self._on_clear_all)
        layout.addWidget(self.clear_btn)

        # Bouton Fermer
        self.close_btn = self._header_button("CloseButton", "close", "tip_close", size=13)
        self.close_btn.clicked.connect(self.hide)
        layout.addWidget(self.close_btn)

        return header

    def _create_tabs_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TabsBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 6)
        layout.setSpacing(5)

        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)

        self.tab_all = self._make_tab("tab_all", "clipboard", "all")
        self.tab_pinned = self._make_tab("tab_pinned", "pin_filled", "pinned")
        self.tab_emoji = self._make_tab("tab_emoji", "emoji", "emoji")

        for tab in (self.tab_all, self.tab_pinned, self.tab_emoji):
            layout.addWidget(tab)
        layout.addStretch()
        return bar

    def _make_tab(self, label_key: str, icon_name: str, tab_id: str) -> QPushButton:
        btn = QPushButton(" " + tr(label_key))
        btn.setProperty("class", "TabButton")
        btn.setIcon(get_icon(icon_name, size=15))
        btn.setCheckable(True)
        btn.setChecked(tab_id == "all")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(lambda checked=False, t=tab_id: self._set_tab(t))
        self.tab_group.addButton(btn)
        return btn

    def _create_search_bar(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 4, 12, 6)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText(tr("search_placeholder"))
        self.search_input.addAction(
            get_icon("search", size=15), QLineEdit.ActionPosition.LeadingPosition
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.returnPressed.connect(self._on_search_enter)
        layout.addWidget(self.search_input)
        return container

    def _create_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("FooterBar")
        footer.setFixedHeight(34)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(14, 4, 14, 6)
        layout.setSpacing(7)

        self.status_dot = QLabel()
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setFixedSize(8, 8)
        layout.addWidget(self.status_dot)

        self.count_label = QLabel()
        self.count_label.setObjectName("FooterCount")
        self.count_label.setProperty("class", "FooterLabel")
        layout.addWidget(self.count_label)

        layout.addStretch()

        self.hints_label = QLabel()
        self.hints_label.setProperty("class", "FooterLabel")
        layout.addWidget(self.hints_label)

        return footer

    # ------------------------------------------------------------------
    # Thème dynamique
    # ------------------------------------------------------------------
    def apply_theme(self):
        """(Ré)applique la palette active à toute l'application."""
        palette = get_palette(settings.resolved_theme())
        self._palette = palette

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(palette))

        # Ombre adaptée au thème
        self._shadow.setColor(QColor(0, 0, 0, palette.get("shadow_alpha", 180)))

        # Icônes monochromes teintées selon le thème
        self.close_btn.setIcon(get_icon("close", size=13, color=palette["text_secondary"]))

        # Couleurs des cartes existantes (badges + icônes monochromes)
        for card in self._cards:
            card.apply_theme_colors(palette)

        # En-têtes de catégories d'émojis
        self.emoji_picker.apply_badge_colors(palette["text_secondary"])

        # État de la surveillance (pastille + bouton pause)
        self._refresh_monitoring_ui()
        self._refresh_footer()

    def _on_setting_changed(self, key: str, value):
        if key == "theme":
            self.apply_theme()
        elif key == "show_hints":
            self._refresh_footer()
        elif key == "monitor_paused":
            self._refresh_monitoring_ui()
            self._refresh_footer()
        elif key == "history_size":
            if self.isVisible():
                self.refresh_clips()

    def _refresh_monitoring_ui(self):
        paused = bool(settings.get("monitor_paused", False))
        self.status_dot.setProperty("paused", paused)
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
        self.pause_btn.setIcon(get_icon("play" if paused else "pause", size=14))
        self.pause_btn.setToolTip(tr("tip_resume") if paused else tr("tip_pause"))

    def _refresh_footer(self):
        paused = bool(settings.get("monitor_paused", False))
        shown = len(self._cards)
        if self.search_text:
            self.count_label.setText(
                tr("footer_count_one" if shown == 1 else "footer_count_many", n=shown)
            )
        else:
            stats = self.db.count_clips()
            total = stats["total"]
            self.count_label.setText(
                tr("footer_count_one" if total == 1 else "footer_count_many", n=total)
            )

        if paused:
            self.hints_label.setText(tr("footer_paused"))
        elif bool(settings.get("show_hints", True)):
            self.hints_label.setText(tr("footer_hints"))
        else:
            self.hints_label.setText("")

    # ------------------------------------------------------------------
    # Onglets & recherche
    # ------------------------------------------------------------------
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
        # Synchroniser l'état visuel des onglets
        for btn, tid in ((self.tab_all, "all"), (self.tab_pinned, "pinned"), (self.tab_emoji, "emoji")):
            btn.setChecked(tid == tab_name)

    def _on_search_changed(self, text: str):
        self.search_text = text.strip()
        self.refresh_clips()

    def _on_search_enter(self):
        """Entrée dans le champ de recherche → colle le résultat sélectionné/top."""
        self._activate_card(self._selected_idx if self._selected_idx >= 0 else 0)

    # ------------------------------------------------------------------
    # Liste des clips
    # ------------------------------------------------------------------
    def refresh_clips(self):
        """Recharge et affiche les éléments filtrés."""
        while self.clips_layout.count() > 0:
            item = self.clips_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()          # évite tout widget « fantôme » visible
                widget.deleteLater()
        self._cards.clear()
        self._clips.clear()

        only_pinned = (self.current_tab == "pinned")
        clips = self.db.get_clips(search=self.search_text, only_pinned=only_pinned)
        self._clips = clips

        palette = getattr(self, "_palette", None) or get_palette(settings.resolved_theme())

        if not clips:
            self.clips_layout.addWidget(self._create_empty_state(only_pinned))
        else:
            for clip in clips:
                card = ClipItemWidget(clip)
                card.apply_theme_colors(palette)
                card.clicked.connect(self._on_item_clicked)
                card.copy_requested.connect(self._copy_only)
                card.pin_toggled.connect(self._on_pin_toggled)
                card.deleted.connect(self._on_item_deleted)
                card.open_requested.connect(self._open_item)
                card.context_requested.connect(self._show_context_menu)
                self.clips_layout.addWidget(card)
                self._cards.append(card)

        # Sélection : première carte par défaut (discrète, sans liseré fort)
        self._selected_idx = 0 if self._cards else -1
        for i, card in enumerate(self._cards):
            card.set_selected(i == self._selected_idx)
        self._refresh_footer()

    def _create_empty_state(self, only_pinned: bool) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 46, 20, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        if self.search_text:
            icon_name, title, sub = "search", tr("empty_search_title"), tr(
                "empty_search_sub", query=self.search_text
            )
        elif only_pinned:
            icon_name, title, sub = "pin_filled", tr("empty_pinned_title"), tr("empty_pinned_sub")
        else:
            icon_name, title, sub = "clipboard", tr("empty_history_title"), tr("empty_history_sub")

        icon_label = QLabel()
        icon_label.setPixmap(create_icon_pixmap(icon_name, size=56))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        lbl_msg = QLabel(title)
        lbl_msg.setProperty("class", "EmptyTitle")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_msg)

        lbl_sub = QLabel(sub)
        lbl_sub.setProperty("class", "EmptySub")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_sub)

        return container

    # ------------------------------------------------------------------
    # Sélection clavier
    # ------------------------------------------------------------------
    def _select(self, idx: int):
        if not self._cards:
            self._selected_idx = -1
            return
        idx = max(0, min(idx, len(self._cards) - 1))
        if idx == self._selected_idx:
            return
        old = self._selected_idx
        self._selected_idx = idx
        if 0 <= old < len(self._cards):
            self._cards[old].set_selected(False)
        self._cards[idx].set_selected(True)
        # Faire défiler jusqu'à la carte sélectionnée
        QTimer.singleShot(0, lambda: self.clips_scroll.ensureWidgetVisible(
            self._cards[idx], 0, 20
        ))

    def _activate_card(self, idx: int):
        if 0 <= idx < len(self._clips):
            self._on_item_clicked(self._clips[idx])

    # ------------------------------------------------------------------
    # Actions sur les éléments
    # ------------------------------------------------------------------
    def _set_clipboard(self, item: dict):
        """Place l'élément dans le presse-papiers système sans boucle."""
        if self.monitor:
            self.monitor.pause_monitoring()
        cb = QGuiApplication.clipboard()
        content_type = item.get("content_type", "text")
        content = item.get("content", "")
        if content_type == "image":
            img = QImage(content)
            if not img.isNull():
                cb.setImage(img)
            else:
                cb.setText(content)
        else:
            cb.setText(content)
        if self.monitor:
            self.monitor.resume_monitoring()

    def _on_item_clicked(self, item: dict):
        """Clic gauche : copie, ferme, puis colle si l'option est activée."""
        self._set_clipboard(item)
        target_wid = self.target_window_id
        self.hide()
        self.item_pasted.emit(item)

        if settings.get("auto_paste", True):
            QTimer.singleShot(90, lambda: paste_clipboard_to_window(target_wid))
        else:
            self.item_copied.emit(item)

    def _copy_only(self, item: dict):
        """Copie l'élément sans le coller (clic molette / Ctrl+C / menu)."""
        self._set_clipboard(item)
        self.hide()
        self.item_copied.emit(item)

    def _open_item(self, item: dict):
        """Ouvre un lien dans le navigateur ou un emplacement de fichier."""
        content_type = item.get("content_type")
        content = item.get("content", "")
        metadata = item.get("metadata", {})
        self.hide()
        if content_type == "url":
            url = content if "://" in content else "https://" + content
            QDesktopServices.openUrl(QUrl(url))
        elif content_type == "path":
            path = metadata.get("path", content.splitlines()[0] if content else "")
            if path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif content_type == "email":
            QDesktopServices.openUrl(QUrl(f"mailto:{content}"))

    def _on_emoji_selected(self, char: str):
        """Émoji cliqué : inséré directement ou copié, selon les préférences.

        La fenêtre reste ouverte pour permettre les clics multiples.
        """
        action = settings.get("emoji_action", "insert")

        if action == "insert":
            if self.monitor:
                self.monitor.pause_monitoring()
            QGuiApplication.clipboard().setText(char)
            if self.monitor:
                self.monitor.resume_monitoring()
            paste_text_to_window(self.target_window_id, char)
        else:
            if self.monitor:
                self.monitor.pause_monitoring()
            QGuiApplication.clipboard().setText(char)
            if self.monitor:
                self.monitor.resume_monitoring()
            self.item_copied.emit({"content": char, "content_type": "text"})

    # ------------------------------------------------------------------
    # Menu contextuel
    # ------------------------------------------------------------------
    def _show_context_menu(self, item: dict, global_pos: QPoint):
        menu = QMenu(self)

        act_paste = menu.addAction(get_icon("paste", size=14), tr("act_paste"))
        act_paste.triggered.connect(lambda: self._on_item_clicked(item))

        act_copy = menu.addAction(get_icon("copy", size=14), tr("act_copy_only"))
        act_copy.triggered.connect(lambda: self._copy_only(item))

        menu.addSeparator()

        is_pinned = bool(item.get("is_pinned", 0))
        pin_icon = (
            get_icon("pin_filled", size=14) if is_pinned
            else get_icon("pin", size=14, color=self._palette["text_secondary"])
        )
        act_pin = menu.addAction(
            pin_icon,
            tr("act_unpin") if is_pinned else tr("act_pin"),
        )
        act_pin.triggered.connect(lambda: self._on_pin_toggled(item["id"]))

        content_type = item.get("content_type")
        if content_type == "url":
            act_open = menu.addAction(get_icon("open", size=14), tr("act_open_url"))
            act_open.triggered.connect(lambda: self._open_item(item))
        elif content_type == "path":
            act_open = menu.addAction(get_icon("open", size=14), tr("act_open_path"))
            act_open.triggered.connect(lambda: self._open_item(item))
        elif content_type == "email":
            act_open = menu.addAction(get_icon("email", size=14), tr("act_open_url"))
            act_open.triggered.connect(lambda: self._open_item(item))

        menu.addSeparator()
        act_del = menu.addAction(get_icon("trash", size=14), tr("act_delete"))
        act_del.triggered.connect(lambda: self._on_item_deleted(item["id"]))

        menu.exec(global_pos)

    # ------------------------------------------------------------------
    # Actions globales
    # ------------------------------------------------------------------
    def _on_pin_toggled(self, clip_id: int):
        self.db.toggle_pin(clip_id)
        self.refresh_clips()

    def _on_item_deleted(self, clip_id: int):
        self.db.delete_clip(clip_id)
        self.refresh_clips()

    def _on_clear_all(self):
        self.db.clear_all(keep_pinned=True)
        self.refresh_clips()

    def _on_pause_clicked(self):
        paused = bool(settings.get("monitor_paused", False))
        if self.monitor:
            self.monitor.set_paused(not paused)
        else:
            settings.set("monitor_paused", not paused)

    def open_settings(self):
        """Ouvre (ou ramène au premier plan) la fenêtre de paramètres."""
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(self.db, parent=None)
            self._settings_dialog.finished.connect(self._on_settings_closed)
        self._settings_dialog.refresh_stats()
        self._settings_dialog.refresh_startup_status()

        # Positionner près de la fenêtre popup
        geo = self.frameGeometry()
        self._settings_dialog.show()
        x = geo.center().x() - self._settings_dialog.width() // 2
        y = geo.center().y() - self._settings_dialog.height() // 2
        screen = QGuiApplication.screenAt(geo.center()) or QGuiApplication.primaryScreen()
        sg = screen.availableGeometry()
        x = max(sg.left() + 8, min(x, sg.right() - self._settings_dialog.width() - 8))
        y = max(sg.top() + 8, min(y, sg.bottom() - self._settings_dialog.height() - 8))
        self._settings_dialog.move(x, y)
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def _on_settings_closed(self, _result: int):
        # Garder le dialogue en mémoire mais le masquer proprement
        if self._settings_dialog is not None:
            self._settings_dialog.hide()

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def show_near_cursor(self):
        """Affiche la fenêtre popup près du curseur, avec fondu d'ouverture."""
        prev_wid = get_active_window_id()
        if prev_wid and prev_wid != str(self.winId()):
            self.target_window_id = prev_wid

        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        x = cursor_pos.x() + 4
        y = cursor_pos.y() + 4

        if x + self.width() > screen_geo.right():
            x = cursor_pos.x() - self.width() - 4
        if y + self.height() > screen_geo.bottom():
            y = cursor_pos.y() - self.height() - 4

        x = max(screen_geo.left() + 4, min(x, screen_geo.right() - self.width() - 4))
        y = max(screen_geo.top() + 4, min(y, screen_geo.bottom() - self.height() - 4))

        self.move(x, y)

        # Réinitialiser la recherche et rafraîchir
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.search_text = ""
        if self.current_tab == "emoji":
            self._set_tab("all")
        self.refresh_clips()

        self._can_auto_hide = False
        self.show()
        self.raise_()
        self.activateWindow()
        self._fade_in()
        self.search_input.setFocus()
        QTimer.singleShot(600, lambda: setattr(self, "_can_auto_hide", True))

    def _fade_in(self):
        """Fondu d'ouverture rapide (140 ms), ignoré en cas d'échec."""
        try:
            self.setWindowOpacity(0.0)
            anim = QPropertyAnimation(self, b"windowOpacity", self)
            anim.setDuration(140)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            self._fade_anim = anim
        except Exception:
            self.setWindowOpacity(1.0)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_near_cursor()

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_is_dragging", False) and (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        mods = event.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)

        if key == Qt.Key.Key_Escape:
            self.hide()
            return
        if self.current_tab == "emoji":
            super().keyPressEvent(event)
            return

        if key in (Qt.Key.Key_Down, Qt.Key.Key_J) and ctrl:
            self._select(self._selected_idx + 1)
            return
        if key in (Qt.Key.Key_Up, Qt.Key.Key_K) and ctrl:
            self._select(self._selected_idx - 1)
            return
        if key == Qt.Key.Key_Down:
            self._select(self._selected_idx + 1)
            return
        if key == Qt.Key.Key_Up:
            self._select(self._selected_idx - 1)
            return
        if key == Qt.Key.Key_Home:
            self._select(0)
            return
        if key == Qt.Key.Key_End:
            self._select(len(self._cards) - 1)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._activate_card(self._selected_idx if self._selected_idx >= 0 else 0)
            return
        if ctrl and key == Qt.Key.Key_C:
            idx = self._selected_idx if self._selected_idx >= 0 else 0
            if 0 <= idx < len(self._clips):
                self._copy_only(self._clips[idx])
            return
        if ctrl and key == Qt.Key.Key_P:
            idx = self._selected_idx
            if 0 <= idx < len(self._clips):
                self._on_pin_toggled(self._clips[idx]["id"])
            return
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            idx = self._selected_idx
            if 0 <= idx < len(self._clips):
                self._on_item_deleted(self._clips[idx]["id"])
            return
        if ctrl and key == Qt.Key.Key_Comma:
            self.open_settings()
            return

        super().keyPressEvent(event)

    def changeEvent(self, event):
        # Fermeture automatique sur perte de focus (comme Windows),
        # seulement après stabilisation — sauf si les paramètres sont ouverts.
        if event.type() == event.Type.ActivationChange:
            if getattr(self, "_can_auto_hide", False) and not self.isActiveWindow():
                if self._settings_dialog is not None and self._settings_dialog.isVisible():
                    return
                self.hide()
        super().changeEvent(event)
