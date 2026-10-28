"""Module d'injection et de collage automatique (auto-paste) pour Linux."""
import ctypes
import os
import subprocess
import time
from typing import Optional

# Chemin vers xdotool dans ~/.local/bin
XDO_TOOL = os.path.expanduser("~/.local/bin/xdotool")
if not os.path.exists(XDO_TOOL):
    XDO_TOOL = "xdotool"


def get_active_window_id() -> Optional[str]:
    """Récupère l'ID de la fenêtre active sous X11/XWayland."""
    try:
        res = subprocess.run(
            [XDO_TOOL, "getactivewindow"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=0.5
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
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
            ctypes.byref(nitems), ctypes.byref(bytes_after), ctypes.byref(prop)
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


def paste_text_to_window(wid: Optional[str], text: str):
    """Tape ou colle directement du texte dans la fenêtre cible (pour les émojis/icônes multiples)."""
    if not text:
        return

    # Si nous avons l'identifiant de la fenêtre cible
    if wid:
        try:
            # Essai avec xdotool type
            res = subprocess.run(
                [XDO_TOOL, "type", "--window", wid, "--delay", "0", text],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=0.6
            )
            if res.returncode == 0:
                return
        except Exception:
            pass

        # Secours : envoyer un Ctrl+V ciblé
        try:
            subprocess.run(
                [XDO_TOOL, "key", "--window", wid, "--clearmodifiers", "ctrl+v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=0.6
            )
            return
        except Exception:
            pass

    # Secours global
    simulate_ctrl_v()


def paste_clipboard_to_window(wid: Optional[str] = None):
    """Envoie la commande Coller (Ctrl+V) à la fenêtre précédente."""
    if wid:
        try:
            res = subprocess.run(
                [XDO_TOOL, "key", "--window", wid, "--clearmodifiers", "ctrl+v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=0.6
            )
            if res.returncode == 0:
                return
        except Exception:
            pass

    # Essai global avec xdotool
    try:
        res = subprocess.run(
            [XDO_TOOL, "key", "--clearmodifiers", "ctrl+v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=0.6
        )
        if res.returncode == 0:
            return
    except Exception:
        pass

    # Secours universel direct via libXtst / XTestFakeKeyEvent
    simulate_ctrl_v()


def simulate_ctrl_v():
    """Synthétise l'appui sur Ctrl + V via XTest."""
    try:
        x11 = ctypes.CDLL("libX11.so.6")
        xtst = ctypes.CDLL("libXtst.so.6")
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]

        display = x11.XOpenDisplay(None)
        if not display:
            return

        XK_Control_L = 0xFFE3
        XK_v = 0x0076

        kc_ctrl = x11.XKeysymToKeycode(ctypes.c_void_p(display), XK_Control_L)
        kc_v = x11.XKeysymToKeycode(ctypes.c_void_p(display), XK_v)

        # Envoi de Ctrl + V
        xtst.XTestFakeKeyEvent(ctypes.c_void_p(display), kc_ctrl, True, 0)
        xtst.XTestFakeKeyEvent(ctypes.c_void_p(display), kc_v, True, 0)
        xtst.XTestFakeKeyEvent(ctypes.c_void_p(display), kc_v, False, 0)
        xtst.XTestFakeKeyEvent(ctypes.c_void_p(display), kc_ctrl, False, 0)

        x11.XFlush(ctypes.c_void_p(display))
        x11.XCloseDisplay(ctypes.c_void_p(display))
    except Exception:
        pass
