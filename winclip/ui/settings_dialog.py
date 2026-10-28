"""Fenêtre de paramètres de WinClip — style Fluent (sombre/clair).

Sections : Apparence, Comportement, Historique & captures,
Données locales, Démarrage automatique (systemd).
"""
import subprocess

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QCursor, QDesktopServices
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QCheckBox, QComboBox, QSlider, QSpinBox, QFrame,
    QScrollArea, QButtonGroup, QMessageBox,
)

from ..config import DATA_DIR, IMAGES_DIR, HISTORY_MIN, HISTORY_MAX
from ..database import Database, format_bytes
from ..i18n import tr
from ..icons import get_icon, create_icon_pixmap
from ..settings import settings


class _DragHeader(QFrame):
    """En-tête déplaçable (la boîte de dialogue est sans bordure)."""

    def __init__(self, dialog: QDialog, parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self._drag_pos = QPoint()
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self.dialog.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and (event.buttons() & Qt.MouseButton.LeftButton):
            self.dialog.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()


class SettingsDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(tr("settings_title"))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(500, 640)
        self._init_ui()
        self.refresh_stats()
        self.refresh_startup_status()

    # ------------------------------------------------------------------
    def _init_ui(self):
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setObjectName("SettingsContainer")
        outer_layout.addWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 14)
        root.setSpacing(0)

        # --- En-tête ---
        header = _DragHeader(self)
        header.setObjectName("HeaderBar")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 12, 12)
        h_layout.setSpacing(8)

        gear = QLabel()
        gear.setPixmap(create_icon_pixmap("settings", size=20))
        h_layout.addWidget(gear)

        title = QLabel(tr("settings_title"))
        title.setObjectName("SettingsTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        close_btn = QPushButton()
        close_btn.setObjectName("CloseButton")
        close_btn.setProperty("class", "IconButton")
        from ..config import get_palette as _gp
        _pal = _gp(settings.resolved_theme())
        close_btn.setIcon(get_icon("close", size=13, color=_pal["text_secondary"]))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.accept)
        h_layout.addWidget(close_btn)
        root.addWidget(header)

        # --- Corps défilant ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(16, 10, 16, 6)
        self.body_layout.setSpacing(12)

        self._build_appearance_section()
        self._build_behavior_section()
        self._build_history_section()
        self._build_data_section()
        self._build_startup_section()

        self.body_layout.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # --- Pied : version + fermer ---
        footer = QHBoxLayout()
        footer.setContentsMargins(18, 10, 18, 0)
        from .. import __version__
        version_lbl = QLabel(f"WinClip v{__version__}")
        version_lbl.setProperty("class", "FooterLabel")
        footer.addWidget(version_lbl)
        footer.addStretch()

        close = QPushButton(tr("btn_close"))
        close.setProperty("class", "PrimaryButton")
        close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        root.addLayout(footer)

        # Poser le conteneur via le layout interne du QDialog
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(outer)

    # ------------------------------------------------------------------
    # Helpers de construction
    # ------------------------------------------------------------------
    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setProperty("class", "SettingsCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)
        self.body_layout.addWidget(card)
        return card, lay

    def _section_title(self, text_key: str):
        lbl = QLabel(tr(text_key))
        lbl.setProperty("class", "SectionTitle")
        self.body_layout.addWidget(lbl)

    def _option_row(self, layout: QVBoxLayout, title_key: str,
                    widget: QWidget = None, sub_key: str = None,
                    value_label: QLabel = None) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        title = QLabel(tr(title_key))
        title.setProperty("class", "OptionTitle")
        title.setWordWrap(True)
        texts.addWidget(title)
        if sub_key:
            sub = QLabel(tr(sub_key))
            sub.setProperty("class", "OptionSub")
            sub.setWordWrap(True)
            texts.addWidget(sub)
        row.addLayout(texts, 1)
        if value_label is not None:
            row.addWidget(value_label)
        if widget is not None:
            row.addWidget(widget)
        layout.addLayout(row)
        return row

    @staticmethod
    def _tune_combo(combo: QComboBox):
        """Empêche le combo d'imposer sa largeur au contenu (libellés longs)."""
        combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        combo.setMinimumContentsLength(12)
        combo.setMaximumWidth(250)

    # ------------------------------------------------------------------
    # 1. Apparence
    # ------------------------------------------------------------------
    def _build_appearance_section(self):
        self._section_title("sec_appearance")
        card, lay = self._card()

        # Thème : boutons segmentés
        seg_group = QButtonGroup(self)
        seg_group.setExclusive(True)
        seg_widget = QWidget()
        seg_widget.setStyleSheet("background: transparent;")
        seg_lay = QHBoxLayout(seg_widget)
        seg_lay.setContentsMargins(0, 0, 0, 0)
        seg_lay.setSpacing(4)
        self.theme_buttons = {}
        for value, label_key in (("dark", "theme_dark"), ("light", "theme_light"), ("auto", "theme_auto")):
            btn = QPushButton(tr(label_key))
            btn.setProperty("class", "SegmentedButton")
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setChecked(settings.get("theme") == value)
            btn.clicked.connect(lambda checked=False, v=value: self._on_theme_changed(v))
            seg_group.addButton(btn)
            seg_lay.addWidget(btn)
            self.theme_buttons[value] = btn
        self._option_row(lay, "opt_theme", widget=seg_widget)

        # Langue : liste déroulante
        self.lang_combo = QComboBox()
        self._tune_combo(self.lang_combo)
        self.lang_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        for value, label_key in (("auto", "lang_auto"), ("fr", "lang_fr"), ("en", "lang_en")):
            self.lang_combo.addItem(tr(label_key), value)
            if settings.get("language") == value:
                self.lang_combo.setCurrentIndex(self.lang_combo.count() - 1)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self._option_row(lay, "opt_language", widget=self.lang_combo)

        self.restart_note = QLabel(tr("restart_note"))
        self.restart_note.setObjectName("RestartNote")
        self.restart_note.setWordWrap(True)
        self.restart_note.setVisible(False)
        lay.addWidget(self.restart_note)

        # Astuces clavier
        self.hints_check = QCheckBox(tr("opt_show_hints"))
        self.hints_check.setChecked(bool(settings.get("show_hints", True)))
        self.hints_check.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hints_check.toggled.connect(
            lambda on: settings.set("show_hints", on)
        )
        lay.addWidget(self.hints_check)

    def _on_theme_changed(self, value: str):
        settings.set("theme", value)
        for v, btn in self.theme_buttons.items():
            btn.setChecked(v == value)

    def _on_language_changed(self, index: int):
        value = self.lang_combo.itemData(index)
        if value and value != settings.get("language"):
            settings.set("language", value)
            self.restart_note.setVisible(True)

    # ------------------------------------------------------------------
    # 2. Comportement
    # ------------------------------------------------------------------
    def _build_behavior_section(self):
        self._section_title("sec_behavior")
        card, lay = self._card()

        self.paste_check = QCheckBox(tr("opt_auto_paste"))
        self.paste_check.setChecked(bool(settings.get("auto_paste", True)))
        self.paste_check.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.paste_check.toggled.connect(lambda on: settings.set("auto_paste", on))
        lay.addWidget(self.paste_check)
        sub = QLabel(tr("opt_auto_paste_sub"))
        sub.setProperty("class", "OptionSub")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        # Action émoji
        self.emoji_combo = QComboBox()
        self._tune_combo(self.emoji_combo)
        self.emoji_combo.addItem(tr("emoji_insert"), "insert")
        self.emoji_combo.addItem(tr("emoji_copy"), "copy")
        if settings.get("emoji_action") == "copy":
            self.emoji_combo.setCurrentIndex(1)
        self.emoji_combo.currentIndexChanged.connect(
            lambda i: settings.set("emoji_action", self.emoji_combo.itemData(i))
        )
        self._option_row(lay, "opt_emoji_action", widget=self.emoji_combo)

        self.sensitive_check = QCheckBox(tr("opt_ignore_sensitive"))
        self.sensitive_check.setChecked(bool(settings.get("ignore_sensitive", True)))
        self.sensitive_check.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sensitive_check.toggled.connect(
            lambda on: settings.set("ignore_sensitive", on)
        )
        lay.addWidget(self.sensitive_check)
        sub2 = QLabel(tr("opt_ignore_sensitive_sub"))
        sub2.setProperty("class", "OptionSub")
        sub2.setWordWrap(True)
        lay.addWidget(sub2)

    # ------------------------------------------------------------------
    # 3. Historique & captures
    # ------------------------------------------------------------------
    def _build_history_section(self):
        self._section_title("sec_history")
        card, lay = self._card()

        # Taille d'historique : curseur + valeur
        self.size_value_lbl = QLabel()
        self.size_value_lbl.setProperty("class", "StatValue")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(HISTORY_MIN, HISTORY_MAX)
        self.size_slider.setSingleStep(25)
        self.size_slider.setPageStep(50)
        self.size_slider.setValue(int(settings.get("history_size", 100)))
        self.size_slider.setMinimumWidth(130)
        self.size_slider.setMaximumWidth(210)
        self.size_slider.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.size_slider.valueChanged.connect(self._on_history_size_changed)
        self._update_size_label(self.size_slider.value())
        self._option_row(lay, "opt_history_size", widget=self.size_slider,
                         value_label=self.size_value_lbl)

        self.images_check = QCheckBox(tr("opt_capture_images"))
        self.images_check.setChecked(bool(settings.get("capture_images", True)))
        self.images_check.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.images_check.toggled.connect(
            lambda on: settings.set("capture_images", on)
        )
        lay.addWidget(self.images_check)

        self.max_img_spin = QSpinBox()
        self.max_img_spin.setRange(1, 100)
        self.max_img_spin.setSuffix(" Mo")
        self.max_img_spin.setValue(int(settings.get("max_image_mb", 10)))
        self.max_img_spin.valueChanged.connect(
            lambda v: settings.set("max_image_mb", v)
        )
        self._option_row(lay, "opt_max_image_mb", widget=self.max_img_spin)

        self.pause_check = QCheckBox(tr("opt_monitor_paused"))
        self.pause_check.setChecked(bool(settings.get("monitor_paused", False)))
        self.pause_check.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pause_check.toggled.connect(
            lambda on: settings.set("monitor_paused", on)
        )
        lay.addWidget(self.pause_check)

    def _on_history_size_changed(self, value: int):
        # Arrondi au pas de 25 pour un réglage propre
        value = max(HISTORY_MIN, min(HISTORY_MAX, round(value / 25) * 25))
        self._update_size_label(value)
        settings.set("history_size", value)
        self.db.cleanup_old_items(value)
        self.refresh_stats()

    def _update_size_label(self, value: int):
        self.size_value_lbl.setText(tr("history_size_value", n=value))

    # ------------------------------------------------------------------
    # 4. Données locales
    # ------------------------------------------------------------------
    def _build_data_section(self):
        self._section_title("sec_data")
        card, lay = self._card()

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        self.stat_clips = QLabel()
        self.stat_db = QLabel()
        self.stat_images = QLabel()
        rows = [
            (tr("data_clips"), self.stat_clips),
            (tr("data_db"), self.stat_db),
            (tr("data_images"), self.stat_images),
        ]
        for r, (name, value_lbl) in enumerate(rows):
            name_lbl = QLabel(name)
            name_lbl.setProperty("class", "OptionSub")
            value_lbl.setProperty("class", "StatValue")
            grid.addWidget(name_lbl, r, 0)
            grid.addWidget(value_lbl, r, 1, Qt.AlignmentFlag.AlignRight)
        grid.setColumnStretch(0, 1)
        lay.addLayout(grid)

        # Rangée 1 : ouverture du dossier + vidage de l'historique
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        open_btn = QPushButton(tr("btn_open_folder"))
        open_btn.setProperty("class", "SettingsButton")
        open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(DATA_DIR)))
        )
        row1.addWidget(open_btn)

        clear_btn = QPushButton(tr("btn_clear_history"))
        clear_btn.setProperty("class", "SettingsButton")
        clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_btn.clicked.connect(self._on_clear_history)
        row1.addWidget(clear_btn)
        row1.addStretch()
        lay.addLayout(row1)

        # Rangée 2 : action destructive isolée
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        delete_btn = QPushButton(tr("btn_delete_all"))
        delete_btn.setProperty("class", "DangerButton")
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.clicked.connect(self._on_delete_all)
        row2.addWidget(delete_btn)
        row2.addStretch()
        lay.addLayout(row2)

    def refresh_stats(self):
        stats = self.db.get_stats()
        pinned_txt = f"  ({stats['pinned']} {tr('data_pinned')})" if stats["pinned"] else ""
        self.stat_clips.setText(f"{stats['clips']}{pinned_txt}")
        self.stat_db.setText(format_bytes(stats["db_bytes"]))
        self.stat_images.setText(
            f"{stats['images_count']} · {format_bytes(stats['images_bytes'])}"
        )

    def _on_clear_history(self):
        self.db.clear_all(keep_pinned=True)
        self.refresh_stats()

    def _on_delete_all(self):
        answer = QMessageBox.question(
            self,
            tr("settings_title"),
            tr("settings_delete_all_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.db.clear_all(keep_pinned=False)
            self.refresh_stats()

    # ------------------------------------------------------------------
    # 5. Démarrage automatique (systemd --user)
    # ------------------------------------------------------------------
    def _build_startup_section(self):
        self._section_title("sec_startup")
        card, lay = self._card()

        self.startup_status = QLabel()
        self.startup_status.setProperty("class", "OptionSub")
        self.startup_status.setWordWrap(True)
        lay.addWidget(self.startup_status)

        self.startup_btn = QPushButton()
        self.startup_btn.setProperty("class", "SettingsButton")
        self.startup_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.startup_btn.clicked.connect(self._on_startup_toggle)
        lay.addWidget(self.startup_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    @staticmethod
    def _systemctl(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["systemctl", "--user", *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=5,
        )

    def refresh_startup_status(self):
        self._startup_active = False
        try:
            res = self._systemctl("is-active", "winclip.service")
            active = res.stdout.strip() == "active"
            known = res.returncode in (0, 3)  # 3 = inactive mais unité connue
            if not known and "could not be found" in (res.stderr or "").lower():
                self.startup_status.setText(tr("startup_unavailable"))
                self.startup_btn.setEnabled(False)
                return
            self._startup_active = active
            self.startup_status.setText(
                tr("startup_active") if active else tr("startup_inactive")
            )
            self.startup_btn.setText(
                tr("btn_startup_disable") if active else tr("btn_startup_enable")
            )
            self.startup_btn.setEnabled(True)
        except (OSError, subprocess.TimeoutExpired):
            self.startup_status.setText(tr("startup_unavailable"))
            self.startup_btn.setEnabled(False)

    def _on_startup_toggle(self):
        try:
            if self._startup_active:
                self._systemctl("disable", "--now", "winclip.service")
            else:
                self._systemctl("enable", "--now", "winclip.service")
        except (OSError, subprocess.TimeoutExpired):
            pass
        self.refresh_startup_status()

    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
