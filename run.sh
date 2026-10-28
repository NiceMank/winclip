#!/usr/bin/env bash
# WinClip — lanceur portable.
# Résout son propre emplacement (même via lien symbolique), prépare
# l'environnement graphique et exécute le démon.
set -euo pipefail

# --- Résolution du répertoire réel de l'application (suit les symlinks) ---
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
APP_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# --- Environnement graphique ---
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
# xcb par défaut : nécessaire à l'auto-collage (xdotool) même sous Wayland.
# Surchargez avec QT_QPA_PLATFORM=wayland si vous savez ce que vous faites.
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"

# --- Interpréteur : venv local prioritaire, sinon python3 système ---
if [ -x "$APP_DIR/.venv/bin/python3" ]; then
  PYTHON="$APP_DIR/.venv/bin/python3"
else
  PYTHON="$(command -v python3 || echo python3)"
fi

exec "$PYTHON" "$APP_DIR/main.py" "$@"
