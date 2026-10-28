"""Styles QSS modernes façon Windows 11 Fluent Dark."""
from ..config import THEME

MAIN_STYLESHEET = f"""
/* Fenêtre principale */
QWidget#MainContainer {{
    background-color: {THEME['bg_main']};
    border: 1px solid {THEME['border']};
    border-radius: 12px;
}}

/* Barre d'en-tête */
QFrame#HeaderBar {{
    background-color: transparent;
    border-bottom: 1px solid {THEME['border']};
    padding: 8px 12px;
}}

QLabel#HeaderTitle {{
    color: {THEME['text_primary']};
    font-size: 14px;
    font-weight: 600;
}}

/* Boutons d'onglets façon Windows 11 */
QPushButton.TabButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: {THEME['text_secondary']};
    font-size: 13px;
    font-weight: 500;
    padding: 6px 14px;
    text-align: center;
}}

QPushButton.TabButton:hover {{
    background-color: {THEME['bg_card_hover']};
    color: {THEME['text_primary']};
}}

QPushButton.TabButton:checked {{
    background-color: {THEME['bg_card']};
    color: {THEME['accent']};
    font-weight: 600;
    border-bottom: 2px solid {THEME['accent']};
}}

/* Bouton de nettoyage */
QPushButton#ClearButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px;
    color: {THEME['text_secondary']};
}}

QPushButton#ClearButton:hover {{
    background-color: rgba(232, 17, 35, 0.15);
    color: {THEME['danger_hover']};
}}

/* Bouton de fermeture */
QPushButton#CloseButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px;
    color: {THEME['text_secondary']};
}}

QPushButton#CloseButton:hover {{
    background-color: {THEME['bg_card_hover']};
    color: {THEME['text_primary']};
}}

/* Champ de recherche */
QLineEdit#SearchInput {{
    background-color: {THEME['bg_search']};
    border: 1px solid {THEME['border']};
    border-radius: 8px;
    color: {THEME['text_primary']};
    padding: 8px 12px 8px 36px;
    font-size: 13px;
}}

QLineEdit#SearchInput:focus {{
    border: 1px solid {THEME['accent']};
    background-color: {THEME['bg_card']};
}}

QLineEdit#SearchInput::placeholder {{
    color: {THEME['text_muted']};
}}

/* Liste défilante */
QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    margin: 4px 2px 4px 0;
}}

QScrollBar::handle:vertical {{
    background-color: #555555;
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #777777;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Carte de clip */
QFrame.ClipCard {{
    background-color: {THEME['bg_card']};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 10px;
    margin: 4px 6px;
}}

QFrame.ClipCard:hover {{
    background-color: {THEME['bg_card_hover']};
    border: 1px solid #444444;
}}

/* Boutons d'action sur carte */
QPushButton.CardActionBtn {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px;
}}

QPushButton.CardActionBtn:hover {{
    background-color: rgba(255, 255, 255, 0.1);
}}

/* Badge de type */
QLabel.TypeBadge {{
    color: {THEME['text_secondary']};
    font-size: 11px;
    font-weight: 500;
}}

/* Texte de contenu */
QLabel.ContentText {{
    color: {THEME['text_primary']};
    font-size: 13px;
    line-height: 1.4;
}}

/* Code monospace */
QLabel.CodeText {{
    color: #e0e0e0;
    font-family: "DejaVu Sans Mono", "Fira Code", "Courier New", monospace;
    font-size: 12px;
    background-color: #1a1a1a;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 8px;
}}

/* Bouton émoji */
QPushButton.EmojiButton {{
    background-color: {THEME['bg_card']};
    border: 1px solid transparent;
    border-radius: 8px;
    font-size: 20px;
    padding: 6px;
}}

QPushButton.EmojiButton:hover {{
    background-color: {THEME['bg_card_hover']};
    border: 1px solid {THEME['accent']};
}}
"""
