"""Générateur complet des icônes au style authentique Microsoft Segoe Fluent (Windows 11).

Toutes les icônes de l'interface (en-tête, onglets, cartes, menus) sont générées
ici en style monochrome blanc pur haute définition avec transparence.
Grâce à `TINTABLE_ICONS`, WinClip les colore automatiquement et élégamment :
- Blanc/Gris clair en thème sombre
- Anthracite/Gris foncé en thème clair
- Bleu accent lors de la sélection

Usage : python3 assets/make_fluent_icons.py
"""
import math
import os
import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "icons")
os.makedirs(OUT_DIR, exist_ok=True)
SIZE = 96  # Résolution 96x96 avec antialiasing optimal


def base_surface():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)
    ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    return surf, ctx


def rounded_rect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


# 1. Clipboard (Presse-papiers) - Style Segoe Fluent Windows 11
def make_clipboard():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Planchette
    rounded_rect(ctx, 22, 22, 52, 60, 6)
    ctx.stroke()
    
    # Clip supérieur
    rounded_rect(ctx, 34, 12, 28, 16, 4)
    ctx.stroke()
    
    # Lignes intérieures discrètes
    ctx.move_to(34, 46)
    ctx.line_to(62, 46)
    ctx.stroke()
    
    ctx.move_to(34, 58)
    ctx.line_to(62, 58)
    ctx.stroke()
    
    ctx.move_to(34, 70)
    ctx.line_to(52, 70)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "clipboard.png"))


# 2. Pin / Pin filled (Épinglé)
def make_pin(filled=False):
    surf, ctx = base_surface()
    ctx.save()
    ctx.translate(48, 48)
    ctx.rotate(math.radians(-35))

    if filled:
        # Punaise pleine
        rounded_rect(ctx, -14, -26, 28, 10, 3)
        ctx.fill()
        
        ctx.move_to(-12, -16)
        ctx.line_to(-16, 6)
        ctx.line_to(16, 6)
        ctx.line_to(12, -16)
        ctx.close_path()
        ctx.fill()
        
        rounded_rect(ctx, -18, 6, 36, 6, 2)
        ctx.fill()
        
        # Aiguille
        ctx.move_to(-2, 12)
        ctx.line_to(0, 34)
        ctx.line_to(2, 12)
        ctx.close_path()
        ctx.fill()
    else:
        # Punaise contour fin
        ctx.set_line_width(4.5)
        rounded_rect(ctx, -13, -26, 26, 9, 3)
        ctx.stroke()
        
        ctx.move_to(-11, -17)
        ctx.line_to(-15, 6)
        ctx.line_to(15, 6)
        ctx.line_to(11, -17)
        ctx.close_path()
        ctx.stroke()
        
        rounded_rect(ctx, -18, 6, 36, 5, 2)
        ctx.stroke()
        
        # Aiguille
        ctx.move_to(0, 11)
        ctx.line_to(0, 34)
        ctx.stroke()

    ctx.restore()
    name = "pin_filled.png" if filled else "pin.png"
    surf.write_to_png(os.path.join(OUT_DIR, name))


# 3. Emoji (Onglet Emojis)
def make_emoji():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Cercle visage
    ctx.arc(48, 48, 36, 0, 2 * math.pi)
    ctx.stroke()
    
    # Yeux pleins
    ctx.arc(36, 40, 4, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(60, 40, 4, 0, 2 * math.pi)
    ctx.fill()
    
    # Sourire
    ctx.arc(48, 46, 20, math.radians(35), math.radians(145))
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "emoji.png"))


# 4. Settings (Engrenage fin Fluent)
def make_settings():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    cx, cy, r_out, r_in = 48, 48, 36, 28
    dents = 8
    
    ctx.move_to(cx + r_out, cy)
    for i in range(dents):
        angle = (2 * math.pi / dents) * i
        a1 = angle - 0.16
        a2 = angle + 0.16
        a3 = angle + (math.pi / dents) - 0.16
        a4 = angle + (math.pi / dents) + 0.16
        
        ctx.line_to(cx + r_out * math.cos(a1), cy + r_out * math.sin(a1))
        ctx.line_to(cx + r_out * math.cos(a2), cy + r_out * math.sin(a2))
        ctx.line_to(cx + r_in * math.cos(a3), cy + r_in * math.sin(a3))
        ctx.line_to(cx + r_in * math.cos(a4), cy + r_in * math.sin(a4))
    ctx.close_path()
    ctx.stroke()
    
    # Cercle central
    ctx.arc(cx, cy, 14, 0, 2 * math.pi)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "settings.png"))


# 5. Clear (Balai / Corbeille épurée)
def make_clear():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Étoiles scintillantes Segoe
    ctx.save()
    ctx.translate(48, 48)
    ctx.rotate(math.radians(-30))
    # Manche
    rounded_rect(ctx, -3, -34, 6, 40, 3)
    ctx.stroke()
    # Tête
    ctx.move_to(-12, 6)
    ctx.line_to(-18, 28)
    ctx.line_to(18, 28)
    ctx.line_to(12, 6)
    ctx.close_path()
    ctx.stroke()
    ctx.restore()
    
    # Éclat scintillant
    ctx.move_to(70, 24)
    ctx.line_to(74, 16)
    ctx.line_to(78, 24)
    ctx.line_to(86, 28)
    ctx.line_to(78, 32)
    ctx.line_to(74, 40)
    ctx.line_to(70, 32)
    ctx.line_to(62, 28)
    ctx.close_path()
    ctx.fill()

    surf.write_to_png(os.path.join(OUT_DIR, "clear.png"))


# 6. Close (Croix fine)
def make_close():
    surf, ctx = base_surface()
    ctx.set_line_width(5.0)
    
    ctx.move_to(28, 28)
    ctx.line_to(68, 68)
    ctx.stroke()
    
    ctx.move_to(68, 28)
    ctx.line_to(28, 68)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "close.png"))


# 7. Pause / Play
def make_pause():
    surf, ctx = base_surface()
    rounded_rect(ctx, 30, 24, 12, 48, 4)
    ctx.fill()
    rounded_rect(ctx, 54, 24, 12, 48, 4)
    ctx.fill()
    surf.write_to_png(os.path.join(OUT_DIR, "pause.png"))


def make_play():
    surf, ctx = base_surface()
    ctx.move_to(32, 22)
    ctx.line_to(72, 48)
    ctx.line_to(32, 74)
    ctx.close_path()
    ctx.fill()
    surf.write_to_png(os.path.join(OUT_DIR, "play.png"))


# 8. Search (Loupe fine)
def make_search():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    ctx.arc(42, 42, 22, 0, 2 * math.pi)
    ctx.stroke()
    
    ctx.move_to(58, 58)
    ctx.line_to(76, 76)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "search.png"))


# 9. Trash (Supprimer)
def make_trash():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Couvercle
    ctx.move_to(20, 28)
    ctx.line_to(76, 28)
    ctx.stroke()
    
    rounded_rect(ctx, 38, 18, 20, 10, 3)
    ctx.stroke()
    
    # Bac
    ctx.move_to(26, 28)
    ctx.line_to(30, 76)
    ctx.line_to(66, 76)
    ctx.line_to(70, 28)
    ctx.stroke()
    
    # Barres intérieures
    ctx.move_to(40, 38)
    ctx.line_to(40, 66)
    ctx.stroke()
    ctx.move_to(56, 38)
    ctx.line_to(56, 66)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "trash.png"))


# 10. Copy / Paste / Open
def make_copy():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Feuille arrière
    rounded_rect(ctx, 32, 16, 44, 52, 5)
    ctx.stroke()
    
    # Feuille avant (pleine avec masque ou décalée)
    ctx.set_source_rgba(0, 0, 0, 1.0)
    rounded_rect(ctx, 20, 28, 44, 52, 5)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 1.0)
    rounded_rect(ctx, 20, 28, 44, 52, 5)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "copy.png"))


def make_paste():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Planchette
    rounded_rect(ctx, 24, 20, 48, 60, 5)
    ctx.stroke()
    
    rounded_rect(ctx, 36, 12, 24, 14, 3)
    ctx.stroke()
    
    # Document inséré
    ctx.set_source_rgba(0, 0, 0, 1.0)
    rounded_rect(ctx, 34, 34, 36, 42, 4)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 1.0)
    rounded_rect(ctx, 34, 34, 36, 42, 4)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "paste.png"))


def make_open():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Cadre
    ctx.move_to(48, 22)
    ctx.line_to(22, 22)
    ctx.line_to(22, 74)
    ctx.line_to(74, 74)
    ctx.line_to(74, 48)
    ctx.stroke()
    
    # Flèche diagonale
    ctx.move_to(44, 52)
    ctx.line_to(76, 20)
    ctx.stroke()
    ctx.move_to(56, 20)
    ctx.line_to(76, 20)
    ctx.line_to(76, 40)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "open.png"))


# 11. Types de contenu (URLs, Code, Email, Color, Image, Folder, Phone, Text)
def make_url():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Globe fin
    ctx.arc(48, 48, 36, 0, 2 * math.pi)
    ctx.stroke()
    
    ctx.move_to(12, 48)
    ctx.line_to(84, 48)
    ctx.stroke()
    
    # Ellipse verticale
    ctx.save()
    ctx.translate(48, 48)
    ctx.scale(0.5, 1.0)
    ctx.arc(0, 0, 36, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()

    surf.write_to_png(os.path.join(OUT_DIR, "url.png"))


def make_code():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Chevrons </> fins
    # <
    ctx.move_to(36, 32)
    ctx.line_to(22, 48)
    ctx.line_to(36, 64)
    ctx.stroke()
    
    # /
    ctx.move_to(56, 26)
    ctx.line_to(40, 70)
    ctx.stroke()
    
    # >
    ctx.move_to(60, 32)
    ctx.line_to(74, 48)
    ctx.line_to(60, 64)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "code.png"))


def make_email():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    rounded_rect(ctx, 16, 26, 64, 44, 6)
    ctx.stroke()
    
    ctx.move_to(18, 28)
    ctx.line_to(48, 52)
    ctx.line_to(78, 28)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "email.png"))


def make_color():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    # Pipette ou palette fine
    ctx.arc(48, 48, 36, 0, 2 * math.pi)
    ctx.stroke()
    
    ctx.arc(36, 36, 5, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(60, 36, 5, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(48, 64, 5, 0, 2 * math.pi)
    ctx.fill()

    surf.write_to_png(os.path.join(OUT_DIR, "color.png"))


def make_image():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    rounded_rect(ctx, 16, 20, 64, 56, 6)
    ctx.stroke()
    
    ctx.arc(32, 36, 6, 0, 2 * math.pi)
    ctx.stroke()
    
    ctx.move_to(22, 68)
    ctx.line_to(42, 46)
    ctx.line_to(54, 58)
    ctx.line_to(64, 48)
    ctx.line_to(74, 68)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "image.png"))


def make_folder():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    ctx.move_to(18, 30)
    ctx.line_to(38, 30)
    ctx.line_to(46, 38)
    ctx.line_to(78, 38)
    ctx.arc(74, 42, 4, -math.pi/2, 0)
    ctx.line_to(78, 70)
    ctx.arc(74, 66, 4, 0, math.pi/2)
    ctx.line_to(18, 70)
    ctx.arc(22, 66, 4, math.pi/2, math.pi)
    ctx.line_to(18, 34)
    ctx.arc(22, 34, 4, math.pi, 3*math.pi/2)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "folder.png"))


def make_phone():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    rounded_rect(ctx, 28, 16, 40, 64, 8)
    ctx.stroke()
    
    ctx.arc(48, 68, 3, 0, 2 * math.pi)
    ctx.fill()
    ctx.move_to(40, 24)
    ctx.line_to(56, 24)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "phone.png"))


def make_text():
    surf, ctx = base_surface()
    ctx.set_line_width(4.5)
    
    rounded_rect(ctx, 22, 16, 52, 64, 6)
    ctx.stroke()
    
    for y in (32, 44, 56, 68):
        w = 34 if y != 68 else 20
        ctx.move_to(31, y)
        ctx.line_to(31 + w, y)
        ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "text.png"))


def make_check():
    surf, ctx = base_surface()
    ctx.set_line_width(6.0)
    
    ctx.move_to(24, 48)
    ctx.line_to(42, 66)
    ctx.line_to(74, 28)
    ctx.stroke()

    surf.write_to_png(os.path.join(OUT_DIR, "check.png"))


if __name__ == "__main__":
    make_clipboard()
    make_pin(False)
    make_pin(True)
    make_emoji()
    make_settings()
    make_clear()
    make_close()
    make_pause()
    make_play()
    make_search()
    make_trash()
    make_copy()
    make_paste()
    make_open()
    make_url()
    make_code()
    make_email()
    make_color()
    make_image()
    make_folder()
    make_phone()
    make_text()
    make_check()
    print("[✓] Toutes les icônes Segoe Fluent Windows 11 ont été générées avec succès !")
