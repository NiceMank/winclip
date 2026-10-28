#!/usr/bin/env bash
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export QT_QPA_PLATFORM="xcb"
export QT_QPA_PLATFORM="xcb"
export PYTHONPATH="/run/media/niceman/Nice/ProjetsWeb/Outils System/WinClip:$PYTHONPATH"
exec python3 "/run/media/niceman/Nice/ProjetsWeb/Outils System/WinClip/main.py" "$@"
