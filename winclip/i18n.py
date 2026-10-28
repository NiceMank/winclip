"""Internationalisation légère de WinClip (français / anglais).

Usage :
    from .i18n import tr
    label.setText(tr("title"))
    badge.setText(tr("lbl_url", domain="github.com"))

La langue est résolue depuis les préférences utilisateur ("auto" = locale).
"""
from typing import Any

FR = {
    # --- Application / plateau système -------------------------------------
    "app_tooltip": "WinClip — Presse-papier moderne",
    "tray_open": "Presse-papiers (Super+V)",
    "tray_pinned": "Éléments épinglés",
    "tray_emoji": "Émojis & symboles",
    "tray_settings": "Paramètres…",
    "tray_pause": "Suspendre la surveillance",
    "tray_resume": "Reprendre la surveillance",
    "tray_clear": "Vider l'historique",
    "tray_quit": "Quitter WinClip",
    "tray_copied_title": "WinClip",
    "tray_copied_body": "Élément copié dans le presse-papiers",
    "tray_paused_body": "La surveillance du presse-papiers est suspendue",
    "tray_resumed_body": "La surveillance du presse-papiers a repris",

    # --- Fenêtre principale -------------------------------------------------
    "title": "Presse-papiers",
    "tip_clear": "Vider l'historique non épinglé",
    "tip_close": "Fermer (Échap)",
    "tip_settings": "Paramètres",
    "tip_pause": "Suspendre la surveillance",
    "tip_resume": "Reprendre la surveillance",
    "tab_all": "Tout",
    "tab_pinned": "Épinglés",
    "tab_emoji": "Émojis",
    "search_placeholder": "Rechercher dans l'historique…",
    "empty_history_title": "L'historique est vide",
    "empty_history_sub": "Les éléments que vous copiez (Ctrl+C) apparaîtront ici.",
    "empty_pinned_title": "Aucun élément épinglé",
    "empty_pinned_sub": "Épinglez des éléments avec 📌 pour les conserver ici.",
    "empty_search_title": "Aucun résultat",
    "empty_search_sub": "Rien ne correspond à « {query} ».",
    "footer_count_one": "{n} élément",
    "footer_count_many": "{n} éléments",
    "footer_hints": "↑↓ naviguer · ⏎ coller · Échap fermer",
    "footer_paused": "⏸ surveillance en pause",

    # --- Cartes & menu contextuel --------------------------------------------
    "act_paste": "Coller",
    "act_copy_only": "Copier uniquement",
    "act_pin": "Épingler",
    "act_unpin": "Désépingler",
    "act_delete": "Supprimer",
    "act_open_url": "Ouvrir le lien dans le navigateur",
    "act_open_path": "Ouvrir l'emplacement",
    "time_now": "À l'instant",
    "time_min": "Il y a {n} min",
    "time_hour": "Il y a {n} h",
    "time_day": "Il y a {n} j",

    # --- Types de contenu -----------------------------------------------------
    "type_text": "Texte",
    "type_url": "Lien",
    "type_email": "E-mail",
    "type_color": "Couleur",
    "type_code": "Code",
    "type_image": "Image",
    "type_path": "Fichier",
    "type_phone": "Téléphone",
    "lbl_empty": "Vide",
    "lbl_color": "Couleur {value}",
    "lbl_email": "Adresse e-mail",
    "lbl_url": "Lien · {domain}",
    "lbl_phone": "Numéro de téléphone",
    "lbl_path": "Chemin de fichier",
    "lbl_paths": "{n} fichiers",
    "lbl_code": "Code {lang} · {lines} l.",
    "lbl_code_generic": "Code · {lines} l.",
    "lbl_json": "JSON · {lines} l.",
    "lbl_html": "HTML · {lines} l.",
    "lbl_css": "CSS · {lines} l.",
    "lbl_shell": "Script shell · {lines} l.",
    "lbl_sql": "SQL · {lines} l.",
    "lbl_image": "Image · {w}×{h}",
    "lbl_text_lines": "Texte · {lines} l. · {chars} car.",
    "lbl_text_short": "Texte court",

    # --- Sélecteur d'émojis ----------------------------------------------------
    "cat_recent": "Récents",
    "cat_faces": "Visages & émotions",
    "cat_gestures": "Gestes & mains",
    "cat_hearts": "Cœurs & amour",
    "cat_animals": "Animaux & nature",
    "cat_food": "Nourriture & boisson",
    "cat_activities": "Activités & sports",
    "cat_travel": "Voyages & lieux",
    "cat_objects": "Objets",
    "cat_tech": "Tech & outils",
    "cat_symbols": "Symboles & typographie",
    "cat_arrows": "Flèches & maths",
    "emoji_tip": "Insérer {em}",

    # --- Paramètres -------------------------------------------------------------
    "settings_title": "Paramètres",
    "sec_appearance": "Apparence",
    "sec_behavior": "Comportement",
    "sec_history": "Historique & captures",
    "sec_data": "Données locales",
    "sec_startup": "Démarrage automatique",
    "opt_theme": "Thème",
    "theme_dark": "Sombre",
    "theme_light": "Clair",
    "theme_auto": "Auto",
    "opt_language": "Langue",
    "lang_auto": "Auto (système)",
    "lang_fr": "Français",
    "lang_en": "English",
    "opt_show_hints": "Afficher les astuces clavier en bas de la fenêtre",
    "opt_auto_paste": "Coller automatiquement après un clic sur un élément",
    "opt_auto_paste_sub": "Sinon, l'élément est seulement copié dans le presse-papiers.",
    "opt_emoji_action": "Action lors d'un clic sur un émoji",
    "emoji_insert": "Insérer directement dans la fenêtre active",
    "emoji_copy": "Copier seulement dans le presse-papiers",
    "opt_ignore_sensitive": "Ignorer les contenus sensibles (mots de passe)",
    "opt_ignore_sensitive_sub": "KeePassXC, Bitwarden, 1Password et consorts marquent le presse-papiers ; WinClip ne l'enregistrera pas.",
    "opt_history_size": "Taille de l'historique",
    "history_size_value": "{n} éléments",
    "opt_capture_images": "Enregistrer les images et captures d'écran copiées",
    "opt_max_image_mb": "Taille maximale par image (Mo)",
    "opt_monitor_paused": "Suspendre la surveillance du presse-papiers",
    "data_clips": "Éléments enregistrés",
    "data_pinned": "dont épinglés",
    "data_db": "Base de données",
    "data_images": "Dossier d'images",
    "btn_open_folder": "Ouvrir le dossier",
    "btn_clear_history": "Vider l'historique",
    "btn_delete_all": "Tout supprimer",
    "startup_active": "Le service systemd est actif.",
    "startup_inactive": "Le service systemd est inactif.",
    "startup_unavailable": "systemd indisponible sur cette session.",
    "btn_startup_enable": "Activer au démarrage",
    "btn_startup_disable": "Désactiver",
    "btn_close": "Fermer",
    "restart_note": "ℹ️ Le changement de langue s'applique au prochain lancement.",
    "settings_delete_all_confirm": "Supprimer définitivement TOUS les éléments, y compris les épinglés ?",

    # --- Divers ------------------------------------------------------------------
    "welcome_text": (
        "👋 Bienvenue dans WinClip 2 !\n\n"
        "• Super+V ouvre ce panneau où que vous soyez\n"
        "• Cliquez sur une carte pour coller son contenu\n"
        "• 📌 épingle vos éléments fréquents\n"
        "• ⚙️ ouvre les paramètres (thème clair, langue, historique…)\n\n"
        "Astuce : naviguez au clavier avec ↑ ↓ puis ⏎."
    ),
}

EN = {
    # --- Application / system tray -------------------------------------------
    "app_tooltip": "WinClip — Modern clipboard manager",
    "tray_open": "Clipboard (Super+V)",
    "tray_pinned": "Pinned items",
    "tray_emoji": "Emojis & symbols",
    "tray_settings": "Settings…",
    "tray_pause": "Pause monitoring",
    "tray_resume": "Resume monitoring",
    "tray_clear": "Clear history",
    "tray_quit": "Quit WinClip",
    "tray_copied_title": "WinClip",
    "tray_copied_body": "Item copied to the clipboard",
    "tray_paused_body": "Clipboard monitoring is paused",
    "tray_resumed_body": "Clipboard monitoring resumed",

    # --- Main window ----------------------------------------------------------
    "title": "Clipboard",
    "tip_clear": "Clear unpinned history",
    "tip_close": "Close (Esc)",
    "tip_settings": "Settings",
    "tip_pause": "Pause monitoring",
    "tip_resume": "Resume monitoring",
    "tab_all": "All",
    "tab_pinned": "Pinned",
    "tab_emoji": "Emojis",
    "search_placeholder": "Search history…",
    "empty_history_title": "History is empty",
    "empty_history_sub": "Items you copy (Ctrl+C) will show up here.",
    "empty_pinned_title": "No pinned items",
    "empty_pinned_sub": "Pin items with 📌 to keep them here.",
    "empty_search_title": "No results",
    "empty_search_sub": "Nothing matches “{query}”.",
    "footer_count_one": "{n} item",
    "footer_count_many": "{n} items",
    "footer_hints": "↑↓ navigate · ⏎ paste · Esc close",
    "footer_paused": "⏸ monitoring paused",

    # --- Cards & context menu ---------------------------------------------------
    "act_paste": "Paste",
    "act_copy_only": "Copy only",
    "act_pin": "Pin",
    "act_unpin": "Unpin",
    "act_delete": "Delete",
    "act_open_url": "Open link in browser",
    "act_open_path": "Open location",
    "time_now": "Just now",
    "time_min": "{n} min ago",
    "time_hour": "{n} h ago",
    "time_day": "{n} d ago",

    # --- Content types -----------------------------------------------------------
    "type_text": "Text",
    "type_url": "Link",
    "type_email": "Email",
    "type_color": "Color",
    "type_code": "Code",
    "type_image": "Image",
    "type_path": "File",
    "type_phone": "Phone",
    "lbl_empty": "Empty",
    "lbl_color": "Color {value}",
    "lbl_email": "Email address",
    "lbl_url": "Link · {domain}",
    "lbl_phone": "Phone number",
    "lbl_path": "File path",
    "lbl_paths": "{n} files",
    "lbl_code": "{lang} code · {lines} l.",
    "lbl_code_generic": "Code · {lines} l.",
    "lbl_json": "JSON · {lines} l.",
    "lbl_html": "HTML · {lines} l.",
    "lbl_css": "CSS · {lines} l.",
    "lbl_shell": "Shell script · {lines} l.",
    "lbl_sql": "SQL · {lines} l.",
    "lbl_image": "Image · {w}×{h}",
    "lbl_text_lines": "Text · {lines} l. · {chars} chars",
    "lbl_text_short": "Short text",

    # --- Emoji picker -------------------------------------------------------------
    "cat_recent": "Recent",
    "cat_faces": "Faces & emotions",
    "cat_gestures": "Gestures & hands",
    "cat_hearts": "Hearts & love",
    "cat_animals": "Animals & nature",
    "cat_food": "Food & drink",
    "cat_activities": "Activities & sports",
    "cat_travel": "Travel & places",
    "cat_objects": "Objects",
    "cat_tech": "Tech & tools",
    "cat_symbols": "Symbols & typography",
    "cat_arrows": "Arrows & math",
    "emoji_tip": "Insert {em}",

    # --- Settings ------------------------------------------------------------------
    "settings_title": "Settings",
    "sec_appearance": "Appearance",
    "sec_behavior": "Behavior",
    "sec_history": "History & captures",
    "sec_data": "Local data",
    "sec_startup": "Autostart",
    "opt_theme": "Theme",
    "theme_dark": "Dark",
    "theme_light": "Light",
    "theme_auto": "Auto",
    "opt_language": "Language",
    "lang_auto": "Auto (system)",
    "lang_fr": "Français",
    "lang_en": "English",
    "opt_show_hints": "Show keyboard hints at the bottom of the window",
    "opt_auto_paste": "Paste automatically after clicking an item",
    "opt_auto_paste_sub": "Otherwise the item is only copied to the clipboard.",
    "opt_emoji_action": "Action when clicking an emoji",
    "emoji_insert": "Insert directly into the active window",
    "emoji_copy": "Copy to the clipboard only",
    "opt_ignore_sensitive": "Ignore sensitive content (passwords)",
    "opt_ignore_sensitive_sub": "KeePassXC, Bitwarden, 1Password and friends mark the clipboard; WinClip will not store it.",
    "opt_history_size": "History size",
    "history_size_value": "{n} items",
    "opt_capture_images": "Store copied images and screenshots",
    "opt_max_image_mb": "Maximum size per image (MB)",
    "opt_monitor_paused": "Pause clipboard monitoring",
    "data_clips": "Stored items",
    "data_pinned": "pinned",
    "data_db": "Database",
    "data_images": "Images folder",
    "btn_open_folder": "Open folder",
    "btn_clear_history": "Clear history",
    "btn_delete_all": "Delete everything",
    "startup_active": "The systemd service is active.",
    "startup_inactive": "The systemd service is inactive.",
    "startup_unavailable": "systemd is unavailable in this session.",
    "btn_startup_enable": "Enable at startup",
    "btn_startup_disable": "Disable",
    "btn_close": "Close",
    "restart_note": "ℹ️ The language change applies on next start.",
    "settings_delete_all_confirm": "Permanently delete ALL items, including pinned ones?",

    # --- Misc -----------------------------------------------------------------------
    "welcome_text": (
        "👋 Welcome to WinClip 2!\n\n"
        "• Super+V opens this panel anywhere\n"
        "• Click a card to paste its content\n"
        "• 📌 pins your frequent items\n"
        "• ⚙️ opens settings (light theme, language, history…)\n\n"
        "Tip: navigate with the keyboard using ↑ ↓ then ⏎."
    ),
}

_TRANSLATIONS = {"fr": FR, "en": EN}
_current_lang = "fr"


def set_language(lang: str) -> None:
    """Définit la langue active ('fr' ou 'en')."""
    global _current_lang
    _current_lang = lang if lang in _TRANSLATIONS else "fr"


def get_language() -> str:
    return _current_lang


def tr(key: str, **kwargs: Any) -> str:
    """Traduit `key` dans la langue active, avec formatage optionnel."""
    table = _TRANSLATIONS.get(_current_lang, FR)
    text = table.get(key) or FR.get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
