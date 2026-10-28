#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$HOME/.local/bin"
APPS_PATH="$HOME/.local/share/applications"

echo "=== Installation et Configuration de WinClip ==="

# 1. Créer le lien symbolique dans ~/.local/bin
mkdir -p "$BIN_PATH"
ln -sf "$SCRIPT_DIR/run.sh" "$BIN_PATH/winclip"
chmod +x "$BIN_PATH/winclip"
echo "[✓] Commande 'winclip' installée dans $BIN_PATH"

# 2. Installer le lanceur d'application (.desktop)
mkdir -p "$APPS_PATH"
cp "$SCRIPT_DIR/winclip.desktop" "$APPS_PATH/winclip.desktop"
sed -i "s|Exec=.*|Exec=$BIN_PATH/winclip toggle|g" "$APPS_PATH/winclip.desktop"
update-desktop-database "$APPS_PATH" 2>/dev/null || true
echo "[✓] Raccourci d'application installé dans le menu GNOME"

# 3. Libérer Super+V du panneau de notification GNOME (qui utilise aussi Super+M)
echo "[-] Libération de Super+V dans GNOME..."
gsettings set org.gnome.shell.keybindings toggle-message-tray "['<Super>m']" 2>/dev/null || true

# 4. Configurer le raccourci clavier global Super+V dans GNOME
echo "[-] Configuration du raccourci clavier Super+V dans GNOME..."

python3 - << 'EOF'
import os
import subprocess
import ast

bin_path = os.path.expanduser('~/.local/bin')

def run_gsettings(args):
    cmd = ['gsettings'] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.stdout.strip()

# Lire la liste actuelle des raccourcis personnalisés
current_val = run_gsettings(['get', 'org.gnome.settings-daemon.plugins.media-keys', 'custom-keybindings'])
try:
    bindings = ast.literal_eval(current_val)
    if not isinstance(bindings, list):
        bindings = []
except Exception:
    bindings = []

target_slot = None
# Vérifier si un slot WinClip existe déjà
for slot in bindings:
    name = run_gsettings(['get', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{slot}', 'name']).strip("'\"")
    if name == 'WinClip':
        target_slot = slot
        break

# Sinon trouver le prochain numéro disponible
if not target_slot:
    existing_nums = []
    for s in bindings:
        part = s.rstrip('/').split('/')[-1]
        if part.startswith('custom'):
            try:
                existing_nums.append(int(part.replace('custom', '')))
            except ValueError:
                pass
    next_num = max(existing_nums, default=-1) + 1
    target_slot = f"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{next_num}/"
    bindings.append(target_slot)
    
    # Mettre à jour la liste principale
    run_gsettings(['set', 'org.gnome.settings-daemon.plugins.media-keys', 'custom-keybindings', str(bindings)])

# Définir les propriétés du raccourci
run_gsettings(['set', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{target_slot}', 'name', 'WinClip'])
run_gsettings(['set', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{target_slot}', 'command', f"{bin_path}/winclip toggle"])
run_gsettings(['set', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{target_slot}', 'binding', '<Super>v'])

print(f"[✓] Raccourci Super+V configuré sur le slot {target_slot}")
EOF

# 5. Configurer et activer le service utilisateur systemd
echo "[-] Activation du service d'arrière-plan WinClip..."
mkdir -p "$HOME/.config/systemd/user"
cat << 'SERVICE_EOF' > "$HOME/.config/systemd/user/winclip.service"
[Unit]
Description=WinClip Clipboard Manager
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=simple
ExecStart=/home/niceman/.local/bin/winclip --daemon
Restart=always
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
SERVICE_EOF

systemctl --user daemon-reload
systemctl --user enable --now winclip.service 2>/dev/null || true
echo "[✓] Service WinClip actif et configuré au démarrage"

echo ""
echo "=== Terminé avec succès ! ==="
echo "Vous pouvez désormais appuyer sur Super + V (Touche Windows + V) pour ouvrir votre presse-papier."
