"""Module d'injection et de collage automatique (auto-paste) pour Linux.

Chaîne de backends, du plus fiable au plus exotique :
  1. xdotool  — X11 / XWayland (recommandé, installé par setup_shortcut.sh)
  2. ydotool  — Wayland natif (nécessite le démon ydotoold)
  3. wtype    — Wayland natif (frappe de texte uniquement)
  4. XTest    — synthèse directe via libXtst (ctypes, X11)

Toutes les tentatives sont journalisées dans ~/.cache/winclip/winclip.log.
"""
import ctypes
import os
import shutil
import subprocess
from typing import Optional

from .logging_util import log_message


def _find_binary(name: str) -> Optional[str]:
    """Localise un binaire : PATH d'abord, puis ~/.local/bin."""
    found = shutil.which(name)
    if found:
        return found
    candidate = os.path.expanduser(f"~/.local/bin/{name}")
    if os.path.exists(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return None


XDO_TOOL = _find_binary("xdotool")
YDO_TOOL = _find_binary("ydotool")
W_TYPE = _find_binary("wtype")


def _is_wayland() -> bool:
    return bool(os.environ.get("WAYLAND_DISPLAY")) and not os.environ.get("DISPLAY")


def _run(cmd: list[str], timeout: float = 0.8) -> bool:
    """Exécute une commande silencieusement ; True si succès."""
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return res.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def get_active_window_id() -> Optional[str]:
    """Récupère l'ID de la fenêtre active sous X11/XWayland."""
    if XDO_TOOL:
        try:
            res = subprocess.run(
                [XDO_TOOL, "getactivewindow"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=0.5,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass

    # Secours via ctypes libX11
    try:
        x11 = ctypes.CDLL("libX11.so.6")
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XDefaultRootWindow.restype = ctypes.c_ulong
        x11.XInternAtom.restype = ctypes.c_ulong
        x11.XGetWindowProperty.restype = ctypes.c_int

        display = x11.XOpenDisplay(None)
        if not display:
            return None

        root = x11.XDefaultRootWindow(display)
        net_active = x11.XInternAtom(display, b"_NET_ACTIVE_WINDOW", False)

        actual_type = ctypes.c_ulong()
        actual_format = ctypes.c_int()
        nitems = ctypes.c_ulong()
        bytes_after = ctypes.c_ulong()
        prop = ctypes.c_void_p()

        status = x11.XGetWindowProperty(
            display, root, net_active, 0, 1, False, 33,
            ctypes.byref(actual_type), ctypes.byref(actual_format),
            ctypes.byref(nitems), ctypes.byref(bytes_after), ctypes.byref(prop),
        )

        wid = None
        if status == 0 and prop.value:
            val = ctypes.cast(prop, ctypes.POINTER(ctypes.c_ulong)).contents.value
            if val:
                wid = str(val)

        x11.XCloseDisplay(display)
        return wid
    except Exception:
        return None


def paste_text_to_window(wid: Optional[str], text: str) -> bool:
    """Frappe directement du texte dans la fenêtre cible (émojis, symboles)."""
    if not text:
        return False

    # 1. xdotool type (X11) — le plus universel
    if XDO_TOOL and wid:
        if _run([XDO_TOOL, "type", "--window", wid, "--delay", "0", "--", text]):
            return True
    if XDO_TOOL:
        if _run([XDO_TOOL, "type", "--delay", "0", "--", text]):
            return True

    # 2. wtype (Wayland natif)
    if W_TYPE and _run([W_TYPE, "--", text]):
        return True

    # 3. Repli : copier puis Ctrl+V
    try:
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(text)
    except Exception:
        pass
    return paste_clipboard_to_window(wid)


def paste_clipboard_to_window(wid: Optional[str] = None) -> bool:
    """Envoie la commande Coller (Ctrl+V) à la fenêtre cible ou active."""
    # 1. xdotool ciblé puis global (X11 / XWayland)
    if XDO_TOOL:
        if wid and _run([XDO_TOOL, "key", "--window", wid, "--clearmodifiers", "ctrl+v"]):
            return True
        if _run([XDO_TOOL, "key", "--clearmodifiers", "ctrl+v"]):
            return True

    # 2. ydotool (Wayland natif, codes clavier Linux : 29=ctrl, 47=v)
    if YDO_TOOL and _run([YDO_TOOL, "key", "29:1", "47:1", "47:0", "29:0"]):
        return True

    # 3. Synthèse XTest directe via ctypes
    if simulate_ctrl_v():
        return True

    log_message(
        "paste: aucun backend disponible (installez xdotool pour X11, "
        "ydotool ou wtype pour Wayland). L'élément reste copié."
    )
    return False


def simulate_ctrl_v() -> bool:
    """Synthétise l'appui sur Ctrl + V via XTest (libXtst)."""
    try:
        x11 = ctypes.CDLL("libX11.so.6")
        xtst = ctypes.CDLL("libXtst.so.6")
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XKeysymToKeycode.restype = ctypes.c_ubyte
        x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

        display = x11.XOpenDisplay(None)
        if not display:
            return False

        XK_Control_L = 0xFFE3
        XK_v = 0x0076

        kc_ctrl = x11.XKeysymToKeycode(ctypes.c_void_p(display), XK_Control_L)
        kc_v = x11.XKeysymToKeycode(ctypes.c_void_p(display), XK_v)
        if not kc_ctrl or not kc_v:
            x11.XCloseDisplay(display)
            return False

        d = ctypes.c_void_p(display)
        xtst.XTestFakeKeyEvent(d, kc_ctrl, True, 0)
        xtst.XTestFakeKeyEvent(d, kc_v, True, 0)
        xtst.XTestFakeKeyEvent(d, kc_v, False, 0)
        xtst.XTestFakeKeyEvent(d, kc_ctrl, False, 0)

        x11.XFlush(d)
        x11.XCloseDisplay(d)
        return True
    except Exception:
        return False
