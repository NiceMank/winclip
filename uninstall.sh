#!/usr/bin/env bash
# ============================================================================
# WinClip — désinstallation propre
# ----------------------------------------------------------------------------
# Supprime : commande ~/.local/bin/winclip, lanceur .desktop, service
# systemd, raccourcis clavier GNOME.
# Les DONNÉES (historique, images, préférences) sont conservées par défaut.
#   --purge   supprime aussi ~/.local/share/winclip, ~/.config/winclip
#             et ~/.cache/winclip
# ============================================================================
set -euo pipefail

PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1

BIN_PATH="$HOME/.local/bin"
APPS_PATH="$HOME/.local/share/applications"

say() { printf '%s\n' "$*"; }
say "=== Désinstallation de WinClip ==="

# 1. Arrêt du service et du démon
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user disable --now winclip.service 2>/dev/null || true
  rm -f "$HOME/.config/systemd/user/winclip.service"
  systemctl --user daemon-reload 2>/dev/null || true
  say "[✓] Service systemd supprimé"
fi
"$BIN_PATH/winclip" quit 2>/dev/null || true

# 2. Commande
rm -f "$BIN_PATH/winclip"
say "[✓] Commande ~/.local/bin/winclip supprimée"

# 3. Lanceur d'application
rm -f "$APPS_PATH/winclip.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS_PATH" 2>/dev/null || true
fi
say "[✓] Lanceur .desktop supprimé"

# 4. Raccourcis clavier GNOME
if command -v gsettings >/dev/null 2>&1; then
  python3 - << 'PYEOF' || true
import ast, subprocess

def run(args):
    res = subprocess.run(["gsettings"] + args, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    return res.stdout.strip()

value = run(["get", "org.gnome.settings-daemon.plugins.media-keys",
             "custom-keybindings"])
try:
    bindings = ast.literal_eval(value)
    bindings = bindings if isinstance(bindings, list) else []
except Exception:
    bindings = []

remaining = []
for slot in bindings:
    key = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{slot}"
    name = run(["get", key, "name"]).strip("'\"")
    if name in ("WinClip", "WinClip Alt"):
        run(["reset", key, "name"])
        run(["reset", key, "command"])
        run(["reset", key, "binding"])
    else:
        remaining.append(slot)

run(["set", "org.gnome.settings-daemon.plugins.media-keys",
     "custom-keybindings", str(remaining)])
print("[✓] Raccourcis clavier GNOME supprimés")
PYEOF
fi

# 5. Données utilisateur (optionnel)
if [ "$PURGE" = "1" ]; then
  rm -rf "$HOME/.local/share/winclip" "$HOME/.config/winclip" "$HOME/.cache/winclip"
  say "[✓] Données utilisateur purgées (historique, images, préférences)"
else
  say "[-] Données conservées (~/.local/share/winclip, ~/.config/winclip)."
  say "    Purgez-les avec : ./uninstall.sh --purge"
fi

# 6. Socket IPC
rm -f "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/winclip-$(id -u).sock" 2>/dev/null || true

say ""
say "=== WinClip désinstallé ==="
say "Le dossier source du dépôt peut être supprimé manuellement."
