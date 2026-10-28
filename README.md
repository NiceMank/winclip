# 📋 WinClip Linux — Modern Windows 11 Clipboard Manager for Linux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux%20%28GNOME%20%2F%20Wayland%20%2F%20X11%29-brightgreen.svg)]()
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

**WinClip** is a bespoke clipboard manager for Linux that faithfully reproduces the look, feel, and functionality of the modern **Windows 11 clipboard popup (`Win + V`)** with Microsoft Fluent Design icons, smart content detection, emoji/symbol picker, and auto-paste support.

---

## ✨ Features

- 🎯 **Native Windows Shortcuts** : Open anytime using **`Super + V`** (Windows key + V) or **`Ctrl + Alt + V`**.
- 🖱️ **Cursor Positioning & Draggable Window** :
  - Automatically pops up exactly at the mouse cursor position.
  - Smart screen edge detection (keeps the popup completely visible).
  - Can be smoothly dragged and moved anywhere on the screen by clicking on the header.
- 🎨 **Microsoft Fluent Design High-Resolution Icons** :
  - 📋 Clipboard (Blue Fluent board, metallic clip, lined sheet).
  - 📌 Pinned (3D Amber/Gold pushpin with shadow).
  - 😀 Emojis & Symbols (3D radiant yellow face with highlights).
  - 🌐 Web links (3D blue globe with meridians & domain extraction).
  - 💻 Code snippets (Terminal dark window with cyan/purple `< / >` tags).
  - 📧 Email addresses (Emerald/cyan envelope with V-fold).
  - 🎨 Color codes (HEX / RGB) with visual live color swatch.
  - 🖼️ Screenshots & Images (High-definition thumbnails).
  - 📝 Text & Notes (Dog-ear document with character/line count).
  - 🧹 Clear history & 🗑️ Delete items.
- ⚡ **Auto-Paste & Direct Insertion** :
  - Clicking any history item automatically closes the popup and pastes it directly into your active document.
  - In the **Émojis & Icônes** tab, clicking icons directly pastes them without closing the window, enabling multi-click insertions (e.g. `🚀🔥😀`). The window stays open until you click away or hit `Escape`.
- 🔍 **Instant Search** : Real-time filtering through hundreds of copied clips.
- 🛡️ **Lightweight & Persistent** :
  - Local indexed SQLite database.
  - Background daemon managed via `systemd --user` with instant (<1 ms) UNIX socket IPC.
  - System tray icon support.

---

## 🚀 Installation & Quick Start

Clone the repository and run the setup script:

```bash
git clone https://github.com/NiceMank/winclip.git
cd winclip
chmod +x setup_shortcut.sh run.sh main.py
./setup_shortcut.sh
```

The script automatically:
1. Installs the `winclip` executable into `~/.local/bin/`.
2. Adds the application launcher `.desktop` with its high-resolution icon into your GNOME Applications grid.
3. Sets up global GNOME keyboard shortcuts (`Ctrl + Alt + V` and `Super + V`).
4. Configures and starts the background `systemd` user service (`winclip.service`).

---

## ⌨️ Usage

- **Toggle Clipboard** : Press **`Ctrl + Alt + V`** or **`Super + V`** (or run `winclip` in terminal).
- **Paste item** : Click any card in the list.
- **Pin / Unpin** : Click the 📌 icon to save frequent snippets permanently.
- **Clear All** : Click the 🧹 broom icon to clear unpinned history.
- **Close** : Press `Escape` or click anywhere outside the window.

---

## 📦 Requirements

- **Linux** (GNOME, Wayland, or X11)
- **Python 3.10+**
- **PyQt6** (`python3-pyqt6`)
- **Cairo** (`python3-cairo`)
- **Pillow** (`python3-pil`)
- **xdotool** (automatically bundled into user space)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
