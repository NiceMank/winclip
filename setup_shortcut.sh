#!/usr/bin/env bash
# ============================================================================
# WinClip — installation et configuration automatiques
# ----------------------------------------------------------------------------
# Ce script est PORTABLE : aucun chemin utilisateur n'est codé en dur.
#   1. Vérifie les dépendances (python3, PyQt6, xdotool) ;
#   2. installe la commande `winclip` dans ~/.local/bin ;
#   3. installe le lanceur .desktop (menu des applications) ;
#   4. configure les raccourcis GNOME Super+V ET Ctrl+Alt+V ;
#   5. crée et démarre le service utilisateur systemd (démarrage auto).
#
# Options :
#   --venv          crée un venv Python local (.venv) avec PyQt6 via pip
#   --no-service    n'installe pas le service systemd
#   --no-shortcut   ne touche pas aux raccourcis clavier GNOME
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$HOME/.local/bin"
APPS_PATH="$HOME/.local/share/applications"
SYSTEMD_DIR="$HOME/.config/systemd/user"

USE_VENV=0
INSTALL_SERVICE=1
INSTALL_SHORTCUT=1
for arg in "$@"; do
  case "$arg" in
    --venv) USE_VENV=1 ;;
    --no-service) INSTALL_SERVICE=0 ;;
    --no-shortcut) INSTALL_SHORTCUT=0 ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
  esac
done

say()  { printf '%s\n' "$*"; }
ok()   { say "[✓] $*"; }
warn() { say "[!] $*"; }
step() { say ""; say "--- $* ---"; }

say "=== Installation et configuration de WinClip 2 ==="
say "Dossier source : $SCRIPT_DIR"

# ----------------------------------------------------------------------------
step "1. Vérification des dépendances"

# Python >= 3.10
if ! command -v python3 >/dev/null 2>&1; then
  say "ERREUR : python3 est introuvable. Installez Python 3.10 ou plus récent."
  exit 1
fi
PY_VERSION_OK="$(python3 -c 'import sys; print(1 if sys.version_info >= (3,10) else 0)')"
if [ "$PY_VERSION_OK" != "1" ]; then
  say "ERREUR : Python 3.10+ requis (version détectée : $(python3 -V 2>&1))."
  exit 1
fi
ok "Python $(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"

# PyQt6 (système ou venv)
check_pyqt() {
  "$1" -c "import PyQt6.QtWidgets" >/dev/null 2>&1
}
if [ "$USE_VENV" = "1" ]; then
  if [ ! -x "$SCRIPT_DIR/.venv/bin/python3" ]; then
    say "[-] Création du venv .venv…"
    python3 -m venv "$SCRIPT_DIR/.venv"
    "$SCRIPT_DIR/.venv/bin/python3" -m pip install --upgrade pip >/dev/null
    "$SCRIPT_DIR/.venv/bin/python3" -m pip install -r "$SCRIPT_DIR/requirements.txt"
  fi
  check_pyqt "$SCRIPT_DIR/.venv/bin/python3" \
    || { warn "PyQt6 indisponible dans le venv."; exit 1; }
  ok "PyQt6 (venv local)"
elif check_pyqt python3; then
  ok "PyQt6 (système)"
else
  warn "PyQt6 est absent du python3 système."
  say "    Solutions :  sudo apt install python3-pyqt6   (Debian/Ubuntu)"
  say "                 sudo dnf install python3-qt6     (Fedora)"
  say "                 ou relancez ce script avec --venv"
  exit 1
fi

# xdotool (auto-collage sous X11/XWayland)
if command -v xdotool >/dev/null 2>&1 || [ -x "$HOME/.local/bin/xdotool" ]; then
  ok "xdotool (auto-collage)"
else
  warn "xdotool introuvable : l'auto-collage sera limité."
  say "    Installez-le : sudo apt install xdotool / sudo dnf install xdotool"
fi

# ----------------------------------------------------------------------------
step "2. Commande 'winclip' dans ~/.local/bin"
mkdir -p "$BIN_PATH"
chmod +x "$SCRIPT_DIR/run.sh" "$SCRIPT_DIR/main.py"
ln -sf "$SCRIPT_DIR/run.sh" "$BIN_PATH/winclip"
ok "Commande 'winclip' installée ($BIN_PATH/winclip)"

# ----------------------------------------------------------------------------
step "3. Lanceur d'application (.desktop)"
mkdir -p "$APPS_PATH"
sed -e "s|__APP_DIR__|$SCRIPT_DIR|g" "$SCRIPT_DIR/winclip.desktop" \
    > "$APPS_PATH/winclip.desktop"
chmod +x "$APPS_PATH/winclip.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS_PATH" 2>/dev/null || true
fi
ok "Lanceur installé dans le menu des applications"

# ----------------------------------------------------------------------------
if [ "$INSTALL_SHORTCUT" = "1" ]; then
  step "4. Raccourcis clavier GNOME (Super+V et Ctrl+Alt+V)"
  if command -v gsettings >/dev/null 2>&1; then
    # Libère Super+V si le panneau de notifications GNOME l'occupe
    CURRENT_TRAY="$(gsettings get org.gnome.shell.keybindings toggle-message-tray 2>/dev/null || echo '')"
    if echo "$CURRENT_TRAY" | grep -qi "super>v\|<Super>v"; then
      gsettings set org.gnome.shell.keybindings toggle-message-tray "['<Super>m']" 2>/dev/null || true
      say "[-] Super+V libéré du panneau de notifications GNOME"
    fi

    python3 - "$BIN_PATH" << 'PYEOF'
import ast
import subprocess
import sys

bin_path = sys.argv[1]

def run(args):
    res = subprocess.run(["gsettings"] + args, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    return res.stdout.strip()

bindings_value = run(["get", "org.gnome.settings-daemon.plugins.media-keys",
                      "custom-keybindings"])
try:
    bindings = ast.literal_eval(bindings_value)
    if not isinstance(bindings, list):
        bindings = []
except Exception:
    bindings = []

def existing_nums():
    nums = []
    for slot in bindings:
        part = slot.rstrip("/").split("/")[-1]
        if part.startswith("custom"):
            try:
                nums.append(int(part.replace("custom", "")))
            except ValueError:
                pass
    return nums

def slot_for_name(name):
    for slot in bindings:
        key = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{slot}"
        if run(["get", key, "name"]).strip("'\"") == name:
            return slot
    return None

def ensure_slot(name, binding):
    slot = slot_for_name(name)
    if not slot:
        next_num = max(existing_nums(), default=-1) + 1
        slot = (f"/org/gnome/settings-daemon/plugins/media-keys/"
                f"custom-keybindings/custom{next_num}/")
        bindings.append(slot)
        run(["set", "org.gnome.settings-daemon.plugins.media-keys",
             "custom-keybindings", str(bindings)])
    base = (f"org.gnome.settings-daemon.plugins.media-keys."
            f"custom-keybinding:{slot}")
    run(["set", base, "name", name])
    run(["set", base, "command", f"{bin_path}/winclip toggle"])
    run(["set", base, "binding", binding])
    return slot

s1 = ensure_slot("WinClip", "<Super>v")
s2 = ensure_slot("WinClip Alt", "<Ctrl><Alt>v")
print(f"[✓] Raccourci Super+V    → slot {s1}")
print(f"[✓] Raccourci Ctrl+Alt+V → slot {s2}")
PYEOF
  else
    warn "gsettings absent (environnement non-GNOME)."
    say "    Configurez manuellement un raccourci personnalisé :"
    say "      Commande : $BIN_PATH/winclip toggle"
    say "      Touches  : Super+V (ou Ctrl+Alt+V)"
  fi
else
  step "4. Raccourcis clavier ignorés (--no-shortcut)"
fi

# ----------------------------------------------------------------------------
if [ "$INSTALL_SERVICE" = "1" ]; then
  step "5. Service utilisateur systemd (démarrage automatique)"
  if command -v systemctl >/dev/null 2>&1 && [ -d "$HOME/.config" ]; then
    mkdir -p "$SYSTEMD_DIR"
    cat > "$SYSTEMD_DIR/winclip.service" << 'SERVICE_EOF'
[Unit]
Description=WinClip Clipboard Manager
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.local/bin/winclip daemon
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
SERVICE_EOF

    # Variables graphiques visibles du service pour cette session
    systemctl --user import-environment DISPLAY WAYLAND_DISPLAY \
      XDG_RUNTIME_DIR QT_QPA_PLATFORM 2>/dev/null || true
    systemctl --user daemon-reload
    systemctl --user enable winclip.service 2>/dev/null || true
    systemctl --user restart winclip.service 2>/dev/null \
      || warn "Service installé mais non démarré (session graphique inactive ?)"
    ok "Service winclip.service actif et lancé au démarrage"
  else
    warn "systemd indisponible : le démarrage automatique n'a pas été configuré."
    say "    Lancez WinClip manuellement : winclip"
  fi
else
  step "5. Service systemd ignoré (--no-service)"
fi

# ----------------------------------------------------------------------------
say ""
say "=== Terminé avec succès ! ==="
say "Appuyez sur Super+V (ou Ctrl+Alt+V) pour ouvrir votre presse-papier."
say "Commandes utiles :"
say "  winclip status   état du démon et statistiques"
say "  winclip          ouvre/ferme le panneau"
say "  winclip clear    vide l'historique non épinglé"
say ""
say "Pour désinstaller : ./uninstall.sh"
