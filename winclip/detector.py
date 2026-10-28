"""Détection intelligente du type de contenu et métadonnées."""
import re
from urllib.parse import urlparse

# Expressions régulières de détection
URL_REGEX = re.compile(
    r'^(https?://[^\s/$.?#].[^\s]*|www\.[^\s/$.?#].[^\s]*)$',
    re.IGNORECASE
)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
HEX_COLOR_REGEX = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3}|[A-Fa-f0-9]{8})$')
RGB_COLOR_REGEX = re.compile(r'^rgba?\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d.]+\s*)?\)$', re.IGNORECASE)

# Mots-clés de langages de programmation
CODE_KEYWORDS = {
    'def', 'class', 'import', 'from', 'function', 'const', 'let', 'var',
    'return', 'async', 'await', 'export', 'default', 'interface', 'type',
    'struct', 'impl', 'fn', 'pub', 'package', 'public', 'private', 'protected',
    'static', 'final', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE'
}


def detect_content_type(content: str) -> tuple[str, dict]:
    """Analyse le contenu textuel et renvoie (type_name, metadata)."""
    stripped = content.strip()
    metadata = {}

    if not stripped:
        return "text", {"label": "Vide"}

    # 1. Vérification Couleur Hex ou RGB
    if HEX_COLOR_REGEX.match(stripped):
        return "color", {"color": stripped, "label": f"Couleur {stripped}"}
    if RGB_COLOR_REGEX.match(stripped):
        return "color", {"color": stripped, "label": f"Couleur {stripped}"}

    # 2. Vérification Email
    if EMAIL_REGEX.match(stripped):
        return "email", {"email": stripped, "label": "Adresse e-mail"}

    # 3. Vérification URL
    if URL_REGEX.match(stripped):
        try:
            parsed = urlparse(stripped if "://" in stripped else f"https://{stripped}")
            domain = parsed.netloc or stripped
            return "url", {"url": stripped, "domain": domain, "label": f"Lien ({domain})"}
        except Exception:
            return "url", {"url": stripped, "label": "Lien Web"}

    # 4. Vérification Code Source / JSON / Balises
    lines = content.splitlines()

    # Détection JSON ou dictionnaire
    if (stripped.startswith('{') and stripped.endswith('}')) or (stripped.startswith('[') and stripped.endswith(']')):
        if any(char in stripped for char in '":,'):
            return "code", {"lines": len(lines), "label": f"JSON / Données ({len(lines)} l.)"}

    # Détection HTML / XML
    if re.search(r'</?[a-z0-9-]+(\s+[^>]*>|>)|<!DOCTYPE', content, re.IGNORECASE):
        return "code", {"lines": len(lines), "label": f"HTML / Balises ({len(lines)} l.)"}

    # Détection script shell
    if content.startswith('#!/'):
        return "code", {"lines": len(lines), "label": "Script Shell"}

    # Analyse des mots-clés de code
    words = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', content))
    matching_keywords = words.intersection(CODE_KEYWORDS)

    has_code_syntax = bool(re.search(r'[{}\[\]();=><+\-*/:]{2,}|=>|->|\.then\(|\.catch\(', content))

    if len(matching_keywords) >= 2 or (len(matching_keywords) >= 1 and (has_code_syntax or len(lines) > 1)):
        return "code", {
            "lines": len(lines),
            "label": f"Code ({len(lines)} lignes)"
        }

    # 5. Texte standard ou multiligne
    if len(lines) > 1:
        return "text", {
            "lines": len(lines),
            "chars": len(content),
            "label": f"Texte ({len(lines)} lignes)"
        }

    return "text", {
        "lines": 1,
        "chars": len(content),
        "label": "Texte court"
    }
