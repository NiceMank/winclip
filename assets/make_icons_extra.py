#!/usr/bin/env python3
"""Générateur des icônes ajoutées en v2 (Pillow, style Fluent Design).

Icônes produites dans assets/icons/ :
    settings, copy, paste, open, pause, play, phone, folder

Rendu : supersampling 4x (384 px) puis réduction LANCZOS vers 96 px
pour un anticrénelage optimal. Aucune dépendance hors Pillow.

Usage :  python3 assets/make_icons_extra.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "icons")
os.makedirs(OUT_DIR, exist_ok=True)

SIZE = 96       # taille finale
SS = 4          # facteur de supersampling
BIG = SIZE * SS


def new_canvas() -> Image.Image:
    return Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))


def finish(img: Image.Image, name: str, shadow_layer: Image.Image | None = None):
    """Compose l'ombre, réduit et enregistre le PNG final."""
    out = new_canvas()
    if shadow_layer is not None:
        sh_alpha = shadow_layer.split()[3].filter(
            ImageFilter.GaussianBlur(6 * SS)
        ).point(lambda p: int(p * 0.45))
        sh = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 255))
        sh.putalpha(sh_alpha)
        out.alpha_composite(sh, (0, 3 * SS))
    out.alpha_composite(img)
    final = out.resize((SIZE, SIZE), Image.LANCZOS)
    final.save(os.path.join(OUT_DIR, f"{name}.png"))
    print(f"[✓] {name}.png")


def vgrad(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    """Dégradé vertical RGBA de `top` vers `bottom`."""
    grad = Image.new("RGBA", (w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        a = 255 if len(top) < 4 else int(top[3] + (bottom[3] - top[3]) * t)
        for x in range(w):
            grad.putpixel((x, y), (r, g, b, a))
    return grad


def vgrad_fast(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    """Dégradé vertical rapide (colonne 1px étirée)."""
    col = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col.putpixel((0, y), tuple(
            int(top[i] + (bottom[i] - top[i]) * t) for i in range(len(top))
        ))
    return col.resize((w, h))


def mask_rounded(w: int, h: int, radius: int) -> Image.Image:
    """Masque alpha d'un rectangle arrondi de la taille exacte (w, h)."""
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    return mask


def fill_with_gradient(base: Image.Image, box: tuple, radius: int,
                       top: tuple, bottom: tuple) -> Image.Image:
    """Dessine un rectangle arrondi rempli d'un dégradé vertical."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    grad = vgrad_fast(w, h, top, bottom)
    mask = mask_rounded(w, h, radius)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(grad, (x0, y0), mask)
    base.alpha_composite(layer)
    return base


def s(v: float) -> int:
    """Met à l'échelle une coordonnée 96px vers le canvas supersamplé."""
    return int(v * SS)


# ---------------------------------------------------------------------------
def make_settings():
    """Engrenage acier bleuté (paramètres)."""
    img = new_canvas()
    cx = cy = BIG // 2
    r_root, r_top = s(24), s(38)
    teeth = 8
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        base = i * step - math.pi / 2
        for frac, r in ((0.00, r_root), (0.22, r_root), (0.30, r_top),
                        (0.70, r_top), (0.78, r_root)):
            a = base + frac * step
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    mask = Image.new("L", (BIG, BIG), 0)
    dm = ImageDraw.Draw(mask)
    dm.polygon(pts, fill=255)
    dm.ellipse([cx - s(15), cy - s(15), cx + s(15), cy + s(15)], fill=0)

    grad = vgrad_fast(BIG, BIG, (122, 152, 192), (52, 82, 128))
    layer = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    layer.paste(grad, (0, 0), mask)
    img.alpha_composite(layer)

    # Liseré intérieur du trou
    d = ImageDraw.Draw(img)
    d.ellipse([cx - s(15), cy - s(15), cx + s(15), cy + s(15)],
              outline=(230, 240, 250, 200), width=s(2))
    finish(img, "settings", shadow_layer=layer)


def make_copy():
    """Deux feuilles superposées (copier)."""
    img = new_canvas()
    shadow = new_canvas()

    # Feuille arrière (bleutée)
    fill_with_gradient(img, (s(30), s(10), s(82), s(70)), s(8),
                       (159, 184, 216), (110, 147, 196))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((s(30), s(10), s(82), s(70)), radius=s(8),
                        outline=(85, 120, 165, 255), width=s(2))

    # Feuille avant (blanche)
    fill_with_gradient(img, (s(14), s(26), s(66), s(86)), s(8),
                       (252, 252, 254), (226, 230, 238))
    d.rounded_rectangle((s(14), s(26), s(66), s(86)), radius=s(8),
                        outline=(150, 160, 178, 255), width=s(2))

    # Lignes de texte
    for y, w in ((42, 38), (52, 42), (62, 34), (72, 24)):
        d.rounded_rectangle((s(22), s(y), s(22 + w), s(y + 4)), radius=s(2),
                            fill=(168, 182, 202, 255))

    ds = ImageDraw.Draw(shadow)
    ds.rounded_rectangle((s(14), s(26), s(66), s(86)), radius=s(8), fill=(0, 0, 0, 255))
    finish(img, "copy", shadow_layer=shadow)


def make_paste():
    """Planche à pince avec feuille + badge flèche verte (coller)."""
    img = new_canvas()
    shadow = new_canvas()

    # Planche bleue
    fill_with_gradient(img, (s(20), s(14), s(76), s(88)), s(9),
                       (0, 120, 212), (10, 90, 160))
    d = ImageDraw.Draw(img)

    # Feuille blanche
    fill_with_gradient(img, (s(27), s(26), s(69), s(80)), s(5),
                       (250, 251, 253), (228, 232, 240))
    for y, w in ((38, 30), (48, 34), (58, 26)):
        d.rounded_rectangle((s(32), s(y), s(32 + w), s(y + 3.5)), radius=s(1.8),
                            fill=(170, 184, 204, 255))

    # Pince argentée
    fill_with_gradient(img, (s(34), s(8), s(62), s(22)), s(4),
                       (222, 228, 236), (160, 168, 184))
    d.rounded_rectangle((s(41), s(12), s(55), s(18)), radius=s(2),
                        fill=(0, 100, 180, 255))

    # Badge flèche verte (bas-droite)
    bcx, bcy, br = s(70), s(72), s(17)
    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=(16, 124, 16, 255))
    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br],
              outline=(255, 255, 255, 230), width=s(2.5))
    # Flèche vers le bas
    d.line([(bcx, bcy - s(8)), (bcx, bcy + s(5))], fill=(255, 255, 255, 255), width=s(3.5))
    d.polygon([(bcx - s(6), bcy + s(3)), (bcx + s(6), bcy + s(3)), (bcx, bcy + s(10))],
              fill=(255, 255, 255, 255))

    ds = ImageDraw.Draw(shadow)
    ds.rounded_rectangle((s(20), s(14), s(76), s(88)), radius=s(9), fill=(0, 0, 0, 255))
    finish(img, "paste", shadow_layer=shadow)


def make_open():
    """Fenêtre avec flèche sortante (ouvrir dans le navigateur)."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # Cadre arrondi avec ouverture en haut à droite
    box = (s(14), s(22), s(72), s(84))
    d.rounded_rectangle(box, radius=s(9), outline=(0, 120, 212, 255), width=s(6))
    # Effacer le coin haut-droit (porte de sortie de la flèche)
    d.rectangle((s(52), s(16), s(78), s(34)), fill=(0, 0, 0, 0))
    d.line([(s(52), s(22)), (s(63), s(22))], fill=(0, 120, 212, 255), width=s(6))

    # Flèche diagonale sortante
    grad_color = (76, 194, 255)
    d.line([(s(38), s(58)), (s(78), s(18))], fill=grad_color, width=s(7))
    d.polygon([(s(60), s(14)), (s(84), s(14)), (s(84), s(38))], fill=grad_color)
    # Pointe affinée
    d.polygon([(s(64), s(14)), (s(84), s(14)), (s(84), s(34))], fill=(0, 120, 212, 255))

    shadow = new_canvas()
    ds = ImageDraw.Draw(shadow)
    ds.rounded_rectangle(box, radius=s(9), outline=(0, 0, 0, 255), width=s(6))
    finish(img, "open", shadow_layer=shadow)


def make_pause():
    """Deux barres ambre (surveillance en pause)."""
    img = new_canvas()
    shadow = new_canvas()
    d = ImageDraw.Draw(img)
    ds = ImageDraw.Draw(shadow)
    for x0 in (26, 54):
        box = (s(x0), s(20), s(x0 + 16), s(76))
        fill_with_gradient(img, box, s(7), (247, 183, 51), (224, 142, 11))
        ds.rounded_rectangle(box, radius=s(7), fill=(0, 0, 0, 255))
    finish(img, "pause", shadow_layer=shadow)


def make_play():
    """Triangle vert aux coins adoucis (reprendre)."""
    img = new_canvas()
    shadow = new_canvas()

    grad = vgrad_fast(BIG, BIG, (126, 217, 87), (63, 165, 53))
    mask = Image.new("L", (BIG, BIG), 0)
    dm = ImageDraw.Draw(mask)
    pts = [(s(30), s(20)), (s(30), s(76)), (s(80), s(48))]
    dm.polygon(pts, fill=255)
    # Adoucir les pointes
    for p in pts:
        dm.ellipse([p[0] - s(5), p[1] - s(5), p[0] + s(5), p[1] + s(5)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2 * SS))

    layer = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    layer.paste(grad, (0, 0), mask)
    img.alpha_composite(layer)

    ds = ImageDraw.Draw(shadow)
    ds.polygon(pts, fill=(0, 0, 0, 255))
    finish(img, "play", shadow_layer=shadow)


def make_phone():
    """Smartphone avec écran allumé (numéro de téléphone)."""
    img = new_canvas()
    shadow = new_canvas()
    d = ImageDraw.Draw(img)

    # Corps
    fill_with_gradient(img, (s(28), s(6), s(68), s(90)), s(10),
                       (74, 88, 104), (34, 46, 60))
    # Écran
    fill_with_gradient(img, (s(33), s(14), s(63), s(78)), s(6),
                       (76, 194, 255), (0, 120, 212))
    # Haut-parleur
    d.rounded_rectangle((s(42), s(9), s(54), s(11.5)), radius=s(1.2),
                        fill=(200, 210, 222, 255))
    # Barre d'accueil
    d.rounded_rectangle((s(42), s(82), s(54), s(85)), radius=s(1.5),
                        fill=(200, 210, 222, 255))
    # Reflet écran
    d.polygon([(s(33), s(50)), (s(63), s(20)), (s(63), s(32)), (s(33), s(62))],
              fill=(255, 255, 255, 46))

    ds = ImageDraw.Draw(shadow)
    ds.rounded_rectangle((s(28), s(6), s(68), s(90)), radius=s(10), fill=(0, 0, 0, 255))
    finish(img, "phone", shadow_layer=shadow)


def make_folder():
    """Dossier manille façon Windows 11 (chemins de fichiers)."""
    img = new_canvas()
    shadow = new_canvas()
    d = ImageDraw.Draw(img)

    # Partie arrière + onglet
    fill_with_gradient(img, (s(10), s(24), s(50), s(40)), s(6),
                       (240, 198, 96), (224, 176, 64))
    fill_with_gradient(img, (s(10), s(32), s(86), s(82)), s(8),
                       (248, 214, 120), (230, 184, 72))

    # Feuilles dépassant
    d.rounded_rectangle((s(22), s(36), s(74), s(52)), radius=s(3),
                        fill=(250, 250, 252, 255))
    d.rounded_rectangle((s(26), s(32), s(70), s(44)), radius=s(3),
                        fill=(255, 255, 255, 255))

    # Rabat avant
    fill_with_gradient(img, (s(8), s(46), s(88), s(84)), s(8),
                       (255, 231, 154), (245, 200, 76))
    # Ligne d'ombre sous le rabat
    d.line([(s(12), s(47)), (s(84), s(47))], fill=(210, 168, 60, 160), width=s(1.5))

    ds = ImageDraw.Draw(shadow)
    ds.rounded_rectangle((s(8), s(32), s(88), s(84)), radius=s(8), fill=(0, 0, 0, 255))
    finish(img, "folder", shadow_layer=shadow)


if __name__ == "__main__":
    make_settings()
    make_copy()
    make_paste()
    make_open()
    make_pause()
    make_play()
    make_phone()
    make_folder()
    print(f"\nIcônes générées dans {OUT_DIR}")


def make_check():
    """Coche blanche 18 px pour les cases à cocher QSS."""
    small_ss = 6
    size_px = 18
    big = size_px * small_ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = small_ss * 2.4
    pts = [(0.24 * big, 0.52 * big), (0.42 * big, 0.70 * big), (0.78 * big, 0.30 * big)]
    d.line(pts[:2], fill=(255, 255, 255, 255), width=int(w))
    d.line(pts[1:], fill=(255, 255, 255, 255), width=int(w))
    for p in pts:
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2],
                  fill=(255, 255, 255, 255))
    final = img.resize((size_px, size_px), Image.LANCZOS)
    final.save(os.path.join(OUT_DIR, "check.png"))
    print("[✓] check.png")


if __name__ == "__main__":
    make_check()
