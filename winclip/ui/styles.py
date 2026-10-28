"""Feuille de style QSS dynamique — Fluent Design sombre & clair (Windows 11).

`build_stylesheet(palette)` génère l'intégralité du style depuis la palette
active. Appliquée globalement à l'application, elle habille la fenêtre
popup, les cartes, les menus contextuels, le plateau système ET la fenêtre
de paramètres.
"""
from ..icons import ICONS_DIR

# Chemin d'icône échappé pour les url() QSS (les espaces sont tolérés)
_CHECK_URL = str(ICONS_DIR / "check.png").replace("\\", "/")


def build_stylesheet(t: dict) -> str:
    """Construit la feuille de style complète pour une palette donnée."""
    return f"""
/* ============================================================
   Fenêtre principale — conteneur « Mica » arrondi
   ============================================================ */
QWidget#MainContainer {{
    background-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 12px;
}}

QFrame#HeaderBar {{
    background-color: transparent;
    border: none;
    border-bottom: 1px solid {t['border_subtle']};
}}

QLabel#HeaderTitle {{
    color: {t['text_primary']};
    font-size: 14px;
    font-weight: 600;
    background: transparent;
}}

/* ============================================================
   Boutons d'en-tête (icônes)
   ============================================================ */
QPushButton.IconButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 4px;
}}
QPushButton.IconButton:hover {{
    background-color: {t['bg_card_hover']};
}}
QPushButton.IconButton:pressed {{
    background-color: {t['bg_card_selected']};
}}
QPushButton#CloseButton:hover {{
    background-color: {t['danger']};
}}
QPushButton#ClearButton:hover {{
    background-color: rgba(232, 17, 35, 0.18);
}}

/* ============================================================
   Onglets — segmentation « pill » façon Windows 11
   ============================================================ */
QWidget#TabsBar {{
    background-color: transparent;
}}
QPushButton.TabButton {{
    background-color: transparent;
    border: none;
    border-radius: 7px;
    color: {t['text_secondary']};
    font-size: 12.5px;
    font-weight: 500;
    padding: 7px 12px;
}}
QPushButton.TabButton:hover {{
    background-color: {t['bg_card_hover']};
    color: {t['text_primary']};
}}
QPushButton.TabButton:checked {{
    background-color: {t['bg_card']};
    color: {t['text_primary']};
    font-weight: 600;
    border: 1px solid {t['border_subtle']};
}}

/* ============================================================
   Recherche
   ============================================================ */
QLineEdit#SearchInput {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-bottom: 2px solid {t['border']};
    border-radius: 8px;
    color: {t['text_primary']};
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {t['accent']};
}}
QLineEdit#SearchInput:focus {{
    border: 1px solid {t['border_focus']};
    border-bottom: 2px solid {t['border_focus']};
    background-color: {t['bg_input']};
}}
QLineEdit#SearchInput::placeholder {{
    color: {t['text_muted']};
}}

/* ============================================================
   Listes défilantes & barres de défilement fines
   ============================================================ */
QScrollArea {{
    background-color: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 4px 2px 4px 0;
}}
QScrollBar::handle:vertical {{
    background-color: {t['scroll_handle']};
    border-radius: 3px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {t['scroll_handle_hover']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* ============================================================
   Cartes de clip
   ============================================================ */
QFrame.ClipCard {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border_subtle']};
    border-left: 3px solid transparent;
    border-radius: 8px;
}}
QFrame.ClipCard:hover {{
    background-color: {t['bg_card_hover']};
    border: 1px solid {t['border']};
    border-left: 3px solid {t['border']};
}}
QFrame.ClipCard[selected="true"] {{
    background-color: {t['bg_card_selected']};
    border: 1px solid {t['accent_light']};
    border-left: 3px solid {t['accent_light']};
}}
QFrame.ClipCard[pinned="true"] {{
    border-left: 3px solid {t['badge_pinned']};
}}
QFrame.ClipCard[pinned="true"][selected="true"] {{
    border: 1px solid {t['accent_light']};
    border-left: 3px solid {t['badge_pinned']};
}}

QPushButton.CardActionBtn {{
    background-color: transparent;
    border: none;
    border-radius: 5px;
    padding: 3px;
}}
QPushButton.CardActionBtn:hover {{
    background-color: rgba(128, 128, 128, 0.25);
}}
QPushButton#DeleteCardBtn:hover {{
    background-color: rgba(232, 17, 35, 0.25);
}}

QLabel.TypeBadge {{
    color: {t['text_secondary']};
    background-color: transparent;
    font-size: 11px;
    font-weight: 600;
}}
QLabel.TimeLabel {{
    color: {t['text_muted']};
    background-color: transparent;
    font-size: 10.5px;
}}
QLabel.ContentText {{
    color: {t['text_primary']};
    background-color: transparent;
    font-size: 13px;
}}
QLabel.CodeText {{
    color: {t['text_primary']};
    font-family: "JetBrains Mono", "DejaVu Sans Mono", "Fira Code", "Courier New", monospace;
    font-size: 11.5px;
    background-color: {t['bg_code']};
    border: 1px solid {t['border_subtle']};
    border-radius: 6px;
    padding: 7px 9px;
}}
QLabel.UrlText {{
    color: {t['badge_url']};
    background-color: transparent;
    font-size: 12.5px;
}}
QLabel.PathText {{
    color: {t['badge_path']};
    background-color: transparent;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 12px;
}}
QLabel.PhoneText {{
    color: {t['badge_phone']};
    background-color: transparent;
    font-size: 13px;
    font-weight: 600;
}}
QLabel.ColorValue {{
    color: {t['text_primary']};
    background-color: transparent;
    font-weight: 600;
    font-size: 13.5px;
    font-family: "DejaVu Sans Mono", monospace;
}}
QLabel.ImageThumb {{
    border: 1px solid {t['border']};
    border-radius: 6px;
    background-color: {t['bg_code']};
}}

/* ============================================================
   Barre d'état (pied de fenêtre)
   ============================================================ */
QFrame#FooterBar {{
    background-color: transparent;
    border: none;
    border-top: 1px solid {t['border_subtle']};
}}
QLabel.FooterLabel {{
    color: {t['text_muted']};
    background-color: transparent;
    font-size: 10.5px;
}}
QLabel#FooterCount {{
    color: {t['text_secondary']};
    font-weight: 600;
}}
QLabel#StatusDot {{
    border-radius: 4px;
    background-color: {t['success']};
    min-width: 8px; max-width: 8px;
    min-height: 8px; max-height: 8px;
}}
QLabel#StatusDot[paused="true"] {{
    background-color: {t['warning']};
}}

/* ============================================================
   États vides
   ============================================================ */
QLabel.EmptyTitle {{
    color: {t['text_primary']};
    font-size: 14.5px;
    font-weight: 600;
    background: transparent;
}}
QLabel.EmptySub {{
    color: {t['text_muted']};
    font-size: 12px;
    background: transparent;
}}

/* ============================================================
   Sélecteur d'émojis
   ============================================================ */
QPushButton.EmojiButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    font-size: 21px;
    font-family: "Noto Color Emoji", "Twemoji Mozilla", "EmojiOne Color",
                 "Segoe UI Emoji", "Apple Color Emoji", sans-serif;
}}
QPushButton.EmojiButton:hover {{
    background-color: {t['bg_card_hover']};
    border: 1px solid {t['border']};
}}
QPushButton.EmojiButton:pressed {{
    background-color: {t['accent']};
}}
QLabel.CategoryHeader {{
    color: {t['text_secondary']};
    font-size: 11.5px;
    font-weight: 700;
    background: transparent;
    padding: 2px 2px;
}}

/* ============================================================
   Menus contextuels & plateau système
   ============================================================ */
QMenu {{
    background-color: {t['bg_secondary']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    color: {t['text_primary']};
    padding: 5px;
    font-size: 12.5px;
}}
QMenu::item {{
    padding: 7px 24px 7px 12px;
    border-radius: 5px;
    color: {t['text_primary']};
}}
QMenu::item:selected {{
    background-color: {t['accent']};
    color: #ffffff;
}}
QMenu::item:disabled {{
    color: {t['text_muted']};
}}
QMenu::separator {{
    height: 1px;
    background: {t['border']};
    margin: 4px 6px;
}}
QMenu::icon {{
    padding-left: 6px;
}}

/* ============================================================
   Infobulles
   ============================================================ */
QToolTip {{
    background-color: {t['bg_secondary']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 11.5px;
}}

/* ============================================================
   Fenêtre de paramètres
   ============================================================ */
QDialog#SettingsDialog {{
    background-color: {t['bg_main']};
}}
QWidget#SettingsContainer {{
    background-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 12px;
}}
QLabel#SettingsTitle {{
    color: {t['text_primary']};
    font-size: 17px;
    font-weight: 700;
    background: transparent;
}}
QLabel.SectionTitle {{
    color: {t['text_primary']};
    font-size: 13px;
    font-weight: 700;
    background: transparent;
    padding-top: 6px;
}}
QFrame.SettingsCard {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border_subtle']};
    border-radius: 8px;
}}
QLabel.OptionTitle {{
    color: {t['text_primary']};
    font-size: 12.5px;
    font-weight: 600;
    background: transparent;
}}
QLabel.OptionSub {{
    color: {t['text_muted']};
    font-size: 11px;
    background: transparent;
}}
QLabel.StatValue {{
    color: {t['text_primary']};
    font-size: 12.5px;
    font-weight: 600;
    background: transparent;
}}

QCheckBox {{
    color: {t['text_primary']};
    font-size: 12.5px;
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {t['border']};
    background-color: {t['bg_input']};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {t['accent_light']};
}}
QCheckBox::indicator:checked {{
    background-color: {t['accent']};
    border: 1px solid {t['accent']};
    image: url("{_CHECK_URL}");
}}

QComboBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    color: {t['text_primary']};
    padding: 5px 10px;
    font-size: 12.5px;
    min-width: 130px;
}}
QComboBox:hover {{
    border: 1px solid {t['accent_light']};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background-color: {t['bg_secondary']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    color: {t['text_primary']};
    selection-background-color: {t['accent']};
    selection-color: #ffffff;
    outline: none;
    padding: 4px;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {t['border']};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {t['accent']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t['accent_light']};
    border: 2px solid {t['bg_main']};
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 9px;
}}
QSlider::handle:horizontal:hover {{
    background: {t['accent']};
}}

QSpinBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    color: {t['text_primary']};
    padding: 4px 8px;
    font-size: 12.5px;
}}

QPushButton.SettingsButton {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-bottom: 2px solid {t['border']};
    border-radius: 6px;
    color: {t['text_primary']};
    font-size: 12.5px;
    font-weight: 600;
    padding: 7px 16px;
}}
QPushButton.SettingsButton:hover {{
    background-color: {t['bg_card_hover']};
    border-bottom: 2px solid {t['accent_light']};
}}
QPushButton.SettingsButton:pressed {{
    background-color: {t['bg_card_selected']};
}}
QPushButton.SettingsButton:disabled {{
    color: {t['text_muted']};
}}
QPushButton.PrimaryButton {{
    background-color: {t['accent']};
    border: 1px solid {t['accent']};
    border-bottom: 2px solid {t['border_focus']};
    border-radius: 6px;
    color: #ffffff;
    font-size: 12.5px;
    font-weight: 600;
    padding: 7px 18px;
}}
QPushButton.PrimaryButton:hover {{
    background-color: {t['accent_hover']};
}}
QPushButton.DangerButton {{
    background-color: transparent;
    border: 1px solid {t['danger']};
    border-radius: 6px;
    color: {t['danger_hover']};
    font-size: 12.5px;
    font-weight: 600;
    padding: 7px 16px;
}}
QPushButton.DangerButton:hover {{
    background-color: {t['danger']};
    color: #ffffff;
}}
QPushButton.SegmentedButton {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    color: {t['text_secondary']};
    font-size: 12.5px;
    padding: 6px 14px;
}}
QPushButton.SegmentedButton:checked {{
    background-color: {t['accent']};
    border: 1px solid {t['accent']};
    color: #ffffff;
    font-weight: 700;
}}

QLabel#RestartNote {{
    color: {t['warning']};
    font-size: 11px;
    background: transparent;
}}

/* Boîtes de dialogue de confirmation */
QMessageBox {{
    background-color: {t['bg_main']};
}}
QMessageBox QLabel {{
    color: {t['text_primary']};
    font-size: 12.5px;
}}
QMessageBox QPushButton {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    color: {t['text_primary']};
    padding: 6px 18px;
    font-size: 12.5px;
    min-width: 70px;
}}
QMessageBox QPushButton:hover {{
    background-color: {t['bg_card_hover']};
}}
QMessageBox QPushButton:default {{
    border: 1px solid {t['accent']};
}}
"""


# Compatibilité v1 : feuille de style sombre statique
MAIN_STYLESHEET = None


def _lazy_main_stylesheet() -> str:
    global MAIN_STYLESHEET
    if MAIN_STYLESHEET is None:
        from ..config import DARK_PALETTE
        MAIN_STYLESHEET = build_stylesheet(DARK_PALETTE)
    return MAIN_STYLESHEET
