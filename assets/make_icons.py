"""Générateur d'icônes haute fidélité style Microsoft Fluent Design via Cairo."""
import math
import os
import cairo

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(OUT_DIR, exist_ok=True)
SIZE = 96  # Haute résolution (96x96, redimensionné avec netteté)


def rounded_rect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def make_clipboard():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)
    # Planchette bleue
    pat = cairo.LinearGradient(20, 16, 76, 84)
    pat.add_color_stop_rgb(0, 0.0, 0.47, 0.83)   # #0078d4
    pat.add_color_stop_rgb(1, 0.05, 0.32, 0.65)
    ctx.set_source(pat)
    rounded_rect(ctx, 18, 16, 60, 70, 10)
    ctx.fill()

    # Feuille blanche
    ctx.set_source_rgb(0.96, 0.96, 0.98)
    rounded_rect(ctx, 24, 26, 48, 54, 6)
    ctx.fill()

    # Lignes sur la feuille
    ctx.set_source_rgb(0.75, 0.82, 0.92)
    for y in [40, 50, 60, 70]:
        w = 34 if y != 70 else 20
        rounded_rect(ctx, 31, y, w, 4, 2)
        ctx.fill()

    # Clip supérieur argenté
    pat_clip = cairo.LinearGradient(34, 10, 62, 24)
    pat_clip.add_color_stop_rgb(0, 0.85, 0.88, 0.92)
    pat_clip.add_color_stop_rgb(1, 0.65, 0.68, 0.75)
    ctx.set_source(pat_clip)
    rounded_rect(ctx, 34, 10, 28, 14, 4)
    ctx.fill()

    # Anneau métallique
    ctx.set_source_rgb(0.0, 0.47, 0.83)
    rounded_rect(ctx, 41, 14, 14, 6, 2)
    ctx.fill()

    surf.write_to_png(f"{OUT_DIR}/clipboard.png")


def make_pin(filled=False):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    ctx.save()
    ctx.translate(48, 48)
    ctx.rotate(math.radians(-30))

    if filled:
        # Tête de punaise dorée / ambre 3D
        pat = cairo.RadialGradient(0, -10, 2, 0, 0, 26)
        pat.add_color_stop_rgb(0, 1.0, 0.85, 0.3)
        pat.add_color_stop_rgb(0.6, 0.95, 0.6, 0.05)
        pat.add_color_stop_rgb(1, 0.8, 0.4, 0.0)
        ctx.set_source(pat)
        rounded_rect(ctx, -14, -26, 28, 12, 4)
        ctx.fill()

        # Corps
        ctx.move_to(-12, -14)
        ctx.line_to(-16, 6)
        ctx.line_to(16, 6)
        ctx.line_to(12, -14)
        ctx.close_path()
        ctx.fill()

        # Base
        rounded_rect(ctx, -18, 6, 36, 6, 3)
        ctx.fill()

        # Pointe argentée
        pat_needle = cairo.LinearGradient(-2, 12, 4, 34)
        pat_needle.add_color_stop_rgb(0, 0.9, 0.9, 0.95)
        pat_needle.add_color_stop_rgb(1, 0.5, 0.55, 0.65)
        ctx.set_source(pat_needle)
        ctx.move_to(-3, 12)
        ctx.line_to(0, 36)
        ctx.line_to(3, 12)
        ctx.close_path()
        ctx.fill()
    else:
        # Punaise contour moderne
        ctx.set_source_rgba(0.7, 0.7, 0.75, 0.9)
        ctx.set_line_width(4)
        rounded_rect(ctx, -12, -24, 24, 10, 3)
        ctx.stroke()
        ctx.move_to(-10, -14)
        ctx.line_to(-14, 6)
        ctx.line_to(14, 6)
        ctx.line_to(10, -14)
        ctx.close_path()
        ctx.stroke()
        ctx.move_to(-2, 6)
        ctx.line_to(0, 32)
        ctx.line_to(2, 6)
        ctx.stroke()

    ctx.restore()
    surf.write_to_png(f"{OUT_DIR}/pin_filled.png" if filled else f"{OUT_DIR}/pin.png")


def make_emoji():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Visage jaune dégradé radieux 3D
    pat = cairo.RadialGradient(38, 36, 4, 48, 48, 42)
    pat.add_color_stop_rgb(0, 1.0, 0.9, 0.3)
    pat.add_color_stop_rgb(0.7, 1.0, 0.75, 0.05)
    pat.add_color_stop_rgb(1, 0.92, 0.55, 0.0)
    ctx.set_source(pat)
    ctx.arc(48, 48, 40, 0, 2 * math.pi)
    ctx.fill()

    # Yeux brillants
    ctx.set_source_rgb(0.2, 0.15, 0.05)
    ctx.arc(36, 40, 5, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(60, 40, 5, 0, 2 * math.pi)
    ctx.fill()

    # Éclat dans les yeux
    ctx.set_source_rgb(1, 1, 1)
    ctx.arc(34, 38, 2, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(58, 38, 2, 0, 2 * math.pi)
    ctx.fill()

    # Sourire joyeux
    ctx.set_source_rgb(0.25, 0.15, 0.05)
    ctx.set_line_width(4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.arc(48, 46, 22, math.radians(30), math.radians(150))
    ctx.stroke()

    # Joues roses
    ctx.set_source_rgba(1.0, 0.4, 0.4, 0.35)
    ctx.arc(28, 52, 7, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(68, 52, 7, 0, 2 * math.pi)
    ctx.fill()

    surf.write_to_png(f"{OUT_DIR}/emoji.png")


def make_url():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Globe bleu Fluent 3D
    pat = cairo.RadialGradient(36, 36, 6, 48, 48, 40)
    pat.add_color_stop_rgb(0, 0.2, 0.75, 1.0)
    pat.add_color_stop_rgb(0.8, 0.0, 0.48, 0.95)
    pat.add_color_stop_rgb(1, 0.0, 0.32, 0.75)
    ctx.set_source(pat)
    ctx.arc(48, 48, 38, 0, 2 * math.pi)
    ctx.fill()

    # Méridiens et parallèles blancs
    ctx.set_source_rgba(1, 1, 1, 0.8)
    ctx.set_line_width(3.5)
    # Équateur
    ctx.move_to(10, 48)
    ctx.line_to(86, 48)
    ctx.stroke()
    # Parallèles
    ctx.save()
    ctx.translate(48, 48)
    ctx.scale(1, 0.5)
    ctx.arc(0, 0, 38, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()
    # Méridien central
    ctx.save()
    ctx.translate(48, 48)
    ctx.scale(0.48, 1)
    ctx.arc(0, 0, 38, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()

    surf.write_to_png(f"{OUT_DIR}/url.png")


def make_code():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Fenêtre sombre arrondie
    pat = cairo.LinearGradient(16, 16, 80, 80)
    pat.add_color_stop_rgb(0, 0.45, 0.25, 0.75)  # Violet violet Fluent
    pat.add_color_stop_rgb(1, 0.2, 0.1, 0.5)
    ctx.set_source(pat)
    rounded_rect(ctx, 14, 16, 68, 64, 12)
    ctx.fill()

    # Écran sombre
    ctx.set_source_rgb(0.12, 0.1, 0.18)
    rounded_rect(ctx, 18, 22, 60, 52, 8)
    ctx.fill()

    # Chevrons </>
    ctx.set_source_rgb(0.3, 0.85, 1.0)
    ctx.set_line_width(4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    # <
    ctx.move_to(36, 40)
    ctx.line_to(28, 48)
    ctx.line_to(36, 56)
    ctx.stroke()

    # /
    ctx.move_to(52, 38)
    ctx.line_to(44, 58)
    ctx.stroke()

    # >
    ctx.move_to(60, 40)
    ctx.line_to(68, 48)
    ctx.line_to(60, 56)
    ctx.stroke()

    surf.write_to_png(f"{OUT_DIR}/code.png")


def make_email():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Enveloppe avec dégradé émeraude/cyan Fluent
    pat = cairo.LinearGradient(14, 20, 82, 74)
    pat.add_color_stop_rgb(0, 0.05, 0.75, 0.65)
    pat.add_color_stop_rgb(1, 0.0, 0.5, 0.55)
    ctx.set_source(pat)
    rounded_rect(ctx, 14, 22, 68, 52, 10)
    ctx.fill()

    # Volet intérieur
    ctx.set_source_rgb(1, 1, 1)
    rounded_rect(ctx, 20, 26, 56, 32, 4)
    ctx.fill()

    # Pli en V
    ctx.set_source_rgb(0.05, 0.65, 0.55)
    ctx.set_line_width(4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(16, 26)
    ctx.line_to(48, 50)
    ctx.line_to(80, 26)
    ctx.stroke()

    surf.write_to_png(f"{OUT_DIR}/email.png")


def make_color():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Palette en bois clair verni
    pat = cairo.LinearGradient(20, 20, 76, 76)
    pat.add_color_stop_rgb(0, 0.95, 0.78, 0.55)
    pat.add_color_stop_rgb(1, 0.85, 0.62, 0.38)
    ctx.set_source(pat)
    ctx.arc(48, 48, 38, 0, 2 * math.pi)
    ctx.fill()

    # Trou du pouce
    ctx.set_source_rgb(0.12, 0.12, 0.12)
    ctx.arc(64, 48, 8, 0, 2 * math.pi)
    ctx.fill()

    # Taches de peinture vives
    colors = [
        (0.95, 0.2, 0.2),   # Rouge
        (1.0, 0.8, 0.1),    # Jaune
        (0.1, 0.75, 0.3),   # Vert
        (0.1, 0.5, 0.95),   # Bleu
        (0.7, 0.2, 0.85),   # Violet
    ]
    coords = [(32, 28), (48, 22), (30, 48), (34, 68), (52, 70)]
    for (r, g, b), (x, y) in zip(colors, coords):
        ctx.set_source_rgb(r, g, b)
        ctx.arc(x, y, 7, 0, 2 * math.pi)
        ctx.fill()
        # Éclat de lumière
        ctx.set_source_rgba(1, 1, 1, 0.6)
        ctx.arc(x - 2, y - 2, 2, 0, 2 * math.pi)
        ctx.fill()

    surf.write_to_png(f"{OUT_DIR}/color.png")


def make_image():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Cadre photo Fluent
    pat = cairo.LinearGradient(14, 16, 82, 80)
    pat.add_color_stop_rgb(0, 0.95, 0.35, 0.45)
    pat.add_color_stop_rgb(1, 0.75, 0.15, 0.55)
    ctx.set_source(pat)
    rounded_rect(ctx, 14, 16, 68, 64, 10)
    ctx.fill()

    # Soleil / Lune
    ctx.set_source_rgb(1.0, 0.85, 0.2)
    ctx.arc(36, 36, 9, 0, 2 * math.pi)
    ctx.fill()

    # Montagnes
    ctx.set_source_rgb(0.98, 0.98, 1.0)
    ctx.move_to(20, 72)
    ctx.line_to(40, 46)
    ctx.line_to(56, 64)
    ctx.line_to(68, 52)
    ctx.line_to(76, 72)
    ctx.close_path()
    ctx.fill()

    surf.write_to_png(f"{OUT_DIR}/image.png")


def make_text():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Feuille de papier avec coin replié
    pat = cairo.LinearGradient(20, 16, 76, 80)
    pat.add_color_stop_rgb(0, 0.35, 0.7, 0.95)
    pat.add_color_stop_rgb(1, 0.15, 0.5, 0.8)
    ctx.set_source(pat)
    rounded_rect(ctx, 20, 14, 56, 68, 8)
    ctx.fill()

    # Papier blanc intérieur
    ctx.set_source_rgb(0.96, 0.97, 1.0)
    rounded_rect(ctx, 24, 18, 48, 60, 6)
    ctx.fill()

    # Lignes de texte
    ctx.set_source_rgb(0.4, 0.55, 0.75)
    for y, w in [(32, 34), (42, 34), (52, 26), (62, 18)]:
        rounded_rect(ctx, 31, y, w, 4, 2)
        ctx.fill()

    surf.write_to_png(f"{OUT_DIR}/text.png")


def make_trash():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Poubelle rouge vif
    pat = cairo.LinearGradient(24, 20, 72, 80)
    pat.add_color_stop_rgb(0, 0.95, 0.25, 0.25)
    pat.add_color_stop_rgb(1, 0.75, 0.1, 0.15)
    ctx.set_source(pat)

    # Couvercle
    rounded_rect(ctx, 24, 22, 48, 8, 4)
    ctx.fill()
    rounded_rect(ctx, 40, 14, 16, 8, 3)
    ctx.fill()

    # Corps du bac
    ctx.move_to(28, 34)
    ctx.line_to(32, 78)
    ctx.line_to(64, 78)
    ctx.line_to(68, 34)
    ctx.close_path()
    ctx.fill()

    # Rainures verticales blanches
    ctx.set_source_rgba(1, 1, 1, 0.5)
    rounded_rect(ctx, 40, 42, 4, 26, 2)
    ctx.fill()
    rounded_rect(ctx, 52, 42, 4, 26, 2)
    ctx.fill()

    surf.write_to_png(f"{OUT_DIR}/trash.png")


def make_search():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    ctx.save()
    ctx.translate(44, 44)
    ctx.rotate(math.radians(-45))

    # Cercle de la loupe
    pat = cairo.LinearGradient(-26, -26, 26, 26)
    pat.add_color_stop_rgb(0, 0.1, 0.65, 1.0)
    pat.add_color_stop_rgb(1, 0.0, 0.45, 0.85)
    ctx.set_source(pat)
    ctx.set_line_width(8)
    ctx.arc(0, -10, 22, 0, 2 * math.pi)
    ctx.stroke()

    # Verre translucide
    ctx.set_source_rgba(0.2, 0.7, 1.0, 0.25)
    ctx.arc(0, -10, 18, 0, 2 * math.pi)
    ctx.fill()

    # Manche
    pat_manche = cairo.LinearGradient(-4, 12, 4, 38)
    pat_manche.add_color_stop_rgb(0, 0.8, 0.85, 0.9)
    pat_manche.add_color_stop_rgb(1, 0.4, 0.45, 0.55)
    ctx.set_source(pat_manche)
    rounded_rect(ctx, -4, 12, 8, 26, 4)
    ctx.fill()

    ctx.restore()
    surf.write_to_png(f"{OUT_DIR}/search.png")


def make_clear():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surf)

    # Balai / Étoiles de nettoyage
    pat = cairo.LinearGradient(20, 20, 76, 76)
    pat.add_color_stop_rgb(0, 1.0, 0.6, 0.2)
    pat.add_color_stop_rgb(1, 0.9, 0.3, 0.1)
    ctx.set_source(pat)

    ctx.save()
    ctx.translate(48, 48)
    ctx.rotate(math.radians(-35))

    # Manche
    rounded_rect(ctx, -4, -36, 8, 42, 3)
    ctx.fill()
    # Brosse
    pat_brosse = cairo.LinearGradient(-14, 6, 14, 30)
    pat_brosse.add_color_stop_rgb(0, 1.0, 0.85, 0.3)
    pat_brosse.add_color_stop_rgb(1, 0.95, 0.65, 0.1)
    ctx.set_source(pat_brosse)
    ctx.move_to(-8, 6)
    ctx.line_to(-18, 32)
    ctx.line_to(18, 32)
    ctx.line_to(8, 6)
    ctx.close_path()
    ctx.fill()
    ctx.restore()

    # Étoiles étincelles
    ctx.set_source_rgb(1, 0.9, 0.2)
    for cx, cy, r in [(72, 24, 6), (24, 70, 5), (78, 64, 4)]:
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.fill()

    surf.write_to_png(f"{OUT_DIR}/clear.png")


if __name__ == "__main__":
    make_clipboard()
    make_pin(False)
    make_pin(True)
    make_emoji()
    make_url()
    make_code()
    make_email()
    make_color()
    make_image()
    make_text()
    make_trash()
    make_search()
    make_clear()
    print("All Fluent Design icons generated successfully in:", OUT_DIR)
