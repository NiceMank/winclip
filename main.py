#!/usr/bin/env python3
"""Lanceur principal de WinClip."""
import sys
from pathlib import Path

# Ajouter le répertoire courant au PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from winclip.app import main

if __name__ == "__main__":
    main()
