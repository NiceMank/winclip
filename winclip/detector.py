"""Détection intelligente du type de contenu et des métadonnées.

Types reconnus : color, email, url, phone, path, code, text.
Le code est analysé plus finement pour identifier le langage
(Python, JavaScript, JSON, HTML, CSS, Shell, SQL, Rust, Go, Java, C/C++, PHP…).

Chaque résultat fournit :
  - "label"     : libellé prêt à l'affichage (français, compatibilité v1)
  - "label_key" : clé i18n pour libellés traduits
  - "label_args": arguments de formatage du libellé i18n
"""
import json
import re
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Expressions régulières de détection
# ---------------------------------------------------------------------------
URL_REGEX = re.compile(
    r'^(https?://[^\s/$.?#].[^\s]*|www\.[^\s/$.?#].[^\s]*'
    r'|ftp://[^\s/$.?#].[^\s]*)$',
    re.IGNORECASE
)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
HEX_COLOR_REGEX = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3}|[A-Fa-f0-9]{8})$')
RGB_COLOR_REGEX = re.compile(
    r'^rgba?\s*\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*(?:,\s*[\d.]+\s*)?\)$',
    re.IGNORECASE
)
HSL_COLOR_REGEX = re.compile(
    r'^hsla?\s*\(\s*[\d.]+\s*(?:deg)?\s*,\s*[\d.]+%\s*,\s*[\d.]+%\s*(?:,\s*[\d.]+\s*)?\)$',
    re.IGNORECASE
)
PHONE_REGEX = re.compile(r'^\+?[\d][\d\s().\-]{7,24}$')
PATH_REGEX = re.compile(r'^(~|/|\$HOME\b|file://)')

# ---------------------------------------------------------------------------
# Signatures de langages : (nom, [(expression, poids), ...])
# Poids 2 = signature quasi certaine (ex. `def f():` en Python).
# Un langage est retenu des que le score cumule atteint 2.
# ---------------------------------------------------------------------------
LANGUAGE_SIGNATURES: list[tuple[str, list[tuple[str, int]]]] = [
    ("Python", [
        (r'\bdef\s+\w+\s*\(.*\)\s*(->[^:]+)?:', 2),
        (r'\bfrom\s+[\w.]+\s+import\b', 2),
        (r'\bclass\s+\w+\s*(\(.*\))?\s*:', 2),
        (r'\bimport\s+\w+', 1),
        (r'\bself\.', 1),
        (r'\bprint\s*\(', 1),
        (r'\belif\b', 1),
        (r'\b__\w+__\b', 1),
    ]),
    ("JavaScript", [
        (r'\bconsole\.log\s*\(', 2),
        (r'\bconst\s+\w+\s*=', 1),
        (r'\blet\s+\w+\s*=', 1),
        (r'\bfunction\s*\w*\s*\(', 1),
        (r'=>', 1),
        (r'\brequire\s*\(', 1),
        (r'\bexport\s+(default|const|function)\b', 1),
        (r'\.then\s*\(', 1),
    ]),
    ("SQL", [
        (r'\bSELECT\b.+?\bFROM\b', 1),
        (r'\bINSERT\s+INTO\b', 2),
        (r'\bUPDATE\b.+\bSET\b', 1),
        (r'\bDELETE\s+FROM\b', 2),
        (r'\bCREATE\s+TABLE\b', 2),
        (r'\bJOIN\b.+\bON\b', 1),
        (r'\bGROUP\s+BY\b', 1),
        (r'\bWHERE\b', 1),
    ]),
    ("Rust", [
        (r'\bfn\s+\w+\s*\(', 2),
        (r'\blet\s+mut\b', 2),
        (r'\bpub\s+(fn|struct|mod)\b', 2),
        (r'\bimpl\b', 1),
        (r'\buse\s+std::', 2),
    ]),
    ("Go", [
        (r'\bfunc\s+(\(\w+\s+\*?\w+\)\s*)?\w+\s*\(', 2),
        (r'\bpackage\s+main\b', 2),
        (r':=', 1),
        (r'\bfmt\.(Println|Printf)\b', 2),
    ]),
    ("Java", [
        (r'\bSystem\.out\.println\b', 3),
        (r'\bpublic\s+static\s+void\b', 2),
        (r'\bpublic\s+class\b', 2),
        (r'\bprivate\s+\w+\s+\w+\s*\(', 1),
    ]),
    ("C/C++", [
        (r'#include\s*[<"]', 3),
        (r'\bint\s+main\s*\(', 2),
        (r'\bprintf\s*\(', 1),
        (r'\bstd::', 2),
        (r'\bmalloc\s*\(', 1),
    ]),
    ("PHP", [
        (r'<\?php', 3),
        (r'\$\w+\s*=', 1),
        (r'\becho\s+["\']', 1),
    ]),
    ("CSS", [
        (r'@media\b', 2),
        (r'@keyframes\b', 2),
        (r'^\s*[.#]?[\w\-]+\s*\{[^}]*:[^}]*;\s*\}', 1),
        (r'\b(margin|padding|color|background|display|flex|grid)\s*:', 1),
    ]),
    ("Shell", [
        (r'^#!\s*/\S*(ba|z|da)?sh\b', 3),
        (r'\bsudo\b', 1),
        (r'\b(if|then|fi|elif)\b.*;\s*then', 1),
        (r'\bfor\s+\w+\s+in\b.*;\s*do\b', 1),
        (r'\bapt(-get)?\s+(install|update)\b', 1),
        (r'\bsystemctl\b', 1),
        (r'\|\s*(grep|awk|sed|xargs)\b', 1),
    ]),
]

CODE_KEYWORDS = {
    'def', 'class', 'import', 'from', 'function', 'const', 'let', 'var',
    'return', 'async', 'await', 'export', 'default', 'interface', 'type',
    'struct', 'impl', 'fn', 'pub', 'package', 'public', 'private', 'protected',
    'static', 'final', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE',
    'include', 'namespace', 'template', 'func', 'echo', 'printf',
}


def _count_digits(text: str) -> int:
    return sum(c.isdigit() for c in text)


def _is_probable_path(stripped: str) -> bool:
    """Vérifie si le texte ressemble à un chemin de fichier local."""
    if not PATH_REGEX.match(stripped):
        return False
    if '\n' in stripped:
        # Plusieurs lignes : liste de fichiers copiés depuis un gestionnaire
        return all(PATH_REGEX.match(ln.strip()) for ln in stripped.splitlines() if ln.strip())
    if stripped.startswith('file://'):
        return True
    # Un chemin absolu doit ressembler à /quelque/chose (pas juste "/")
    if stripped.startswith('/'):
        return bool(re.match(r'^/[\w.\-~/ ]+', stripped))
    return True


def detect_language(content: str) -> tuple[str, dict] | None:
    """Détecte le langage d'un extrait de code. Renvoie (label_key, args) ou None."""
    stripped = content.strip()
    lines = content.splitlines()
    n_lines = len(lines)

    # JSON valide ?
    if stripped[:1] in '{[' and stripped[-1:] in '}]':
        try:
            json.loads(stripped)
            return "lbl_json", {"lines": n_lines}
        except (json.JSONDecodeError, ValueError):
            pass

    # HTML / XML
    if re.search(r'<!DOCTYPE\s+html', stripped, re.IGNORECASE) or (
        re.search(r'</?[a-z][\w-]*(\s[^>]*)?/?>', content, re.IGNORECASE)
        and re.search(r'</[a-z][\w-]*\s*>', content, re.IGNORECASE)
    ):
        return "lbl_html", {"lines": n_lines}

    # Score par signature de langage
    best_lang, best_score = None, 0
    for lang, patterns in LANGUAGE_SIGNATURES:
        score = 0
        flags = re.IGNORECASE if lang == "SQL" else re.MULTILINE
        for pat, weight in patterns:
            if re.search(pat, content, flags):
                score += weight
        if score > best_score:
            best_lang, best_score = lang, score

    if best_lang and best_score >= 2:
        return "lbl_code", {"lang": best_lang, "lines": n_lines}
    return None


def detect_content_type(content: str) -> tuple[str, dict]:
    """Analyse le contenu textuel et renvoie (type_name, metadata)."""
    stripped = content.strip()

    if not stripped:
        return "text", {"label": "Vide", "label_key": "lbl_empty", "label_args": {}}

    # 1. Couleur (HEX, RGB/RGBA, HSL/HSLA)
    if HEX_COLOR_REGEX.match(stripped) or RGB_COLOR_REGEX.match(stripped) or HSL_COLOR_REGEX.match(stripped):
        return "color", {
            "color": stripped,
            "label": f"Couleur {stripped}",
            "label_key": "lbl_color",
            "label_args": {"value": stripped},
        }

    # 2. Adresse e-mail
    if EMAIL_REGEX.match(stripped):
        return "email", {
            "email": stripped,
            "label": "Adresse e-mail",
            "label_key": "lbl_email",
            "label_args": {},
        }

    # 3. Lien web
    if URL_REGEX.match(stripped) and not stripped.startswith('file://'):
        try:
            parsed = urlparse(stripped if "://" in stripped else f"https://{stripped}")
            domain = parsed.netloc or stripped
        except Exception:
            domain = stripped
        return "url", {
            "url": stripped,
            "domain": domain,
            "label": f"Lien ({domain})",
            "label_key": "lbl_url",
            "label_args": {"domain": domain},
        }

    # 4. Numéro de téléphone (au moins 8 chiffres, format plausible)
    if PHONE_REGEX.match(stripped) and _count_digits(stripped) >= 8:
        return "phone", {
            "phone": stripped,
            "label": "Numéro de téléphone",
            "label_key": "lbl_phone",
            "label_args": {},
        }

    # 5. Chemin(s) de fichier local
    if _is_probable_path(stripped):
        paths = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
        if len(paths) == 1:
            return "path", {
                "path": paths[0],
                "label": "Chemin de fichier",
                "label_key": "lbl_path",
                "label_args": {},
            }
        return "path", {
            "path": paths[0],
            "paths": paths,
            "label": f"{len(paths)} fichiers",
            "label_key": "lbl_paths",
            "label_args": {"n": len(paths)},
        }

    lines = content.splitlines()

    # 6. Code source — détection fine du langage
    lang_result = detect_language(content)
    if lang_result:
        label_key, label_args = lang_result
        from .i18n import tr
        return "code", {
            "lines": len(lines),
            "label": tr(label_key, **label_args),
            "label_key": label_key,
            "label_args": label_args,
        }

    # Détection générique par mots-clés (héritée de la v1, élargie)
    words = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', content))
    matching_keywords = words.intersection(CODE_KEYWORDS)
    has_code_syntax = bool(re.search(
        r'[{}\[\]();=><+\-*/:]{2,}|=>|->|\.then\(|\.catch\(', content
    ))

    if len(matching_keywords) >= 2 or (
        len(matching_keywords) >= 1 and (has_code_syntax or len(lines) > 2)
    ):
        from .i18n import tr
        return "code", {
            "lines": len(lines),
            "label": tr("lbl_code_generic", lines=len(lines)),
            "label_key": "lbl_code_generic",
            "label_args": {"lines": len(lines)},
        }

    # 7. Texte standard
    if len(lines) > 1:
        return "text", {
            "lines": len(lines),
            "chars": len(content),
            "label": f"Texte ({len(lines)} lignes)",
            "label_key": "lbl_text_lines",
            "label_args": {"lines": len(lines), "chars": len(content)},
        }

    return "text", {
        "lines": 1,
        "chars": len(content),
        "label": "Texte court",
        "label_key": "lbl_text_short",
        "label_args": {},
    }
