"""Self-drawn PlayStation button glyphs in Dead Space Ignition's blue button style.

Used by make_button_mods.py when no PS3 copy of the game is given, so the PS3 prompt set needs only
the Xbox 360 files. Original artwork (MIT, Killers' Heaven); no Sony or EA art is copied.
  face(name, size)      round button with a Square / Triangle / Circle / Cross outline symbol
  shoulder(cell, text)  the game's own Xbox shoulder pill with its lettering replaced (L1, R1, L2, R2)
  start(w, h)           PS3-style Start arrow
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from keyboard_glyphs import EDGE, TOP, BOT, INK, SS, _gradient, blank_pill, pill_label

def _finish(img, size):
    small = img.resize(size, Image.BOX)
    a = np.array(small)
    a[a[:, :, 3] < 72] = 0          # DXT3 alpha has 16 steps: drop the faint fringe instead of dithering it
    return Image.fromarray(a, 'RGBA')

def _symbol(d, name, cx, cy, r, t):
    if name == 'Square':
        s = r * 0.62
        d.rectangle((cx - s, cy - s, cx + s, cy + s), outline=INK, width=t)
    elif name == 'Circle':
        s = r * 0.66
        d.ellipse((cx - s, cy - s, cx + s, cy + s), outline=INK, width=t)
    elif name == 'Triangle':
        s = r * 0.80
        pts = [(cx + s * math.cos(math.radians(a)), cy + 0.08 * r + s * math.sin(math.radians(a))) for a in (-90, 30, 150)]
        d.polygon(pts, outline=INK, width=t)
    elif name == 'Cross':
        s = r * 0.56
        d.line((cx - s, cy - s, cx + s, cy + s), fill=INK, width=t)
        d.line((cx - s, cy + s, cx + s, cy - s), fill=INK, width=t)

def face(name, size=33):
    """Round blue button with a PlayStation symbol; `size` is the final cell edge in pixels."""
    S = size * SS
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    inset = 1.5 * SS
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).ellipse((inset, inset, S - inset - 1, S - inset - 1), fill=255)
    img.paste(_gradient(S, S, TOP, BOT), (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.ellipse((inset, inset, S - inset - 1, S - inset - 1), outline=EDGE, width=int(1.6 * SS * size / 33))
    r = (S - 2 * inset) / 2
    _symbol(d, name, S / 2, S / 2, r * 0.82, max(int(2.0 * SS * size / 33), SS))
    return _finish(img, (size, size))

def start(w=43, h=31):
    """Right-pointing Start arrow, filled with the button gradient and rimmed."""
    W, H = w * SS, h * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = 1.5 * SS
    pts = [(m, m), (W - m, H / 2), (m, H - m)]
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    img.paste(_gradient(W, H, TOP, BOT), (0, 0), mask)
    ImageDraw.Draw(img).polygon(pts, outline=EDGE, width=int(1.6 * SS))
    return _finish(img, (w, h))

def shoulder(cell, text):
    """`cell` = the Xbox pill cropped from the same atlas; returns it relabelled with `text`."""
    cell = cell.convert('RGBA')
    out = np.array(pill_label(blank_pill(cell), text))
    out[:, :, 3] = np.array(cell)[:, :, 3]     # keep the pill's own edge: resampled alpha turns dotted in DXT3
    return Image.fromarray(out, 'RGBA')

if __name__ == '__main__':
    import sys
    icons = [face(n) for n in ('Square', 'Triangle', 'Circle', 'Cross')] + [face('Square', 51), start()]
    W = sum(i.width + 8 for i in icons) + 8
    sheet = Image.new('RGBA', (W, 60), (40, 40, 48, 255)); x = 8
    for i in icons:
        sheet.alpha_composite(i, (x, 4)); x += i.width + 8
    sheet.resize((W * 3, 180), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else 'ps3_glyphs_preview.png')
