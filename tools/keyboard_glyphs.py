"""Draw keyboard-key button glyphs in Dead Space Ignition's blue button style.

Face buttons (33x33 cells) become keycaps; shoulder/trigger pills (84x42) reuse the game's own pill art
with the Xbox lettering painted out. Labels follow the ReXGlue keyboard defaults used in play.bat:
  A=Space  B=Backspace  X=L  Y=P  LB=1  RB=3  LT=Q  RT=E
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
EDGE = (189, 218, 230, 255)     # light rim colour sampled from the Xbox icons
TOP = (128, 158, 186, 255)      # fill gradient, top
BOT = (70, 96, 122, 255)        # fill gradient, bottom
INK = (214, 234, 242, 255)      # label colour
SS = 4                          # supersampling factor

def _gradient(w, h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    g = (np.array(top) * (1 - t) + np.array(bot) * t).repeat(w, 1)
    return Image.fromarray(g.astype(np.uint8), 'RGBA')

def keycap(label, size=31, symbol=None, height=None, font_px=15):
    """Rounded-square keycap with a soft outer glow; `symbol` draws Space/Backspace pictograms."""
    W = size * SS; H = (height or size) * SS; S = H
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    r = 7 * SS; inset = 2 * SS
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((inset, inset, W - inset - 1, H - inset - 1), r, fill=255)
    body = _gradient(W, H, TOP, BOT); img.paste(body, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((inset, inset, W - inset - 1, H - inset - 1), r, outline=EDGE, width=int(1.6 * SS))
    cx, cy = W / 2, H / 2 - 1.2 * SS
    if symbol == 'space':      # open-bracket "space bar" pictogram
        w, h, t = 15 * SS, 5 * SS, int(2.2 * SS)
        x0, y0 = cx - w / 2, cy - h / 2 + 2 * SS
        d.line((x0, y0, x0, y0 + h, x0 + w, y0 + h, x0 + w, y0), fill=INK, width=t, joint='curve')
    elif symbol == 'backspace':  # arrow-tag pictogram with an x
        w, h = 17 * SS, 11 * SS
        x0, y0 = cx - w / 2, cy - h / 2
        pts = [(x0, cy), (x0 + 5 * SS, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0 + 5 * SS, y0 + h)]
        d.polygon(pts, outline=INK, width=int(1.8 * SS))
        m = 2.6 * SS; ox = x0 + 10.5 * SS
        d.line((ox - m, cy - m, ox + m, cy + m), fill=INK, width=int(1.8 * SS))
        d.line((ox - m, cy + m, ox + m, cy - m), fill=INK, width=int(1.8 * SS))
    elif symbol == 'enter':      # return-arrow pictogram
        t = int(2.0 * SS)
        x1, y0 = cx + 6 * SS, cy - 6 * SS
        ya = cy + 3 * SS; x0 = cx - 6 * SS
        d.line((x1, y0, x1, ya, x0 + 2 * SS, ya), fill=INK, width=t, joint='curve')
        d.polygon([(x0 - 1 * SS, ya), (x0 + 4 * SS, ya - 4.5 * SS), (x0 + 4 * SS, ya + 4.5 * SS)], fill=INK)
    else:
        f = ImageFont.truetype(FONT, int(font_px * SS))
        d.text((cx, cy), label, font=f, fill=INK, anchor='mm')
    # no soft outer glow: DXT3 stores alpha in 16 steps, which turns a faint glow into a dotted edge
    out = img
    small = out.resize((size, height or size), Image.BOX)
    a = np.array(small)
    a[a[:, :, 3] < 72] = 0          # drop the faint resampling fringe (DXT3 alpha would dither it)
    return Image.fromarray(a, 'RGBA')

def blank_pill(pill):
    """Paint out the light lettering of a game pill by copying each row's colour from the pill's left side."""
    a = np.array(pill.convert('RGBA')).astype(np.int16)
    h, w = a.shape[:2]
    lum = a[:, :, :3].mean(2)
    letters = np.zeros((h, w), bool)
    letters[8:h - 8, 16:w - 16] = lum[8:h - 8, 16:w - 16] > 165
    letters = np.array(Image.fromarray((letters * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    for y in range(h):
        if letters[y].any():
            ref = a[y, 12:15].mean(0)
            a[y, letters[y]] = ref
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')

def pill_label(blank, text):
    S = SS
    big = blank.resize((blank.width * S, blank.height * S), Image.LANCZOS)
    d = ImageDraw.Draw(big)
    f = ImageFont.truetype(FONT, int(22 * S))
    d.text((big.width / 2, big.height / 2 - 1 * S), text, font=f, fill=INK, anchor='mm')
    return big.resize(blank.size, Image.LANCZOS)

FACE = {'A': ('', 'space'), 'B': ('', 'backspace'), 'X': ('L', None), 'Y': ('P', None)}
PILLS = {'LB': '1', 'RB': '3', 'LT': 'Q', 'RT': 'E'}

if __name__ == '__main__':
    # preview sheet
    sheet = Image.new('RGBA', (5 * 40 + 4 * 92, 50), (60, 60, 70, 255))
    for i, (k, (lab, sym)) in enumerate(FACE.items()):
        sheet.alpha_composite(keycap(lab, symbol=sym), (8 + i * 40, 8))
    sheet.save('/root/glyphs/keyboard_preview.png')

def pill_key(text):
    """84x42 shoulder/trigger cell drawn as a wide keycap."""
    return keycap(text, size=82, height=40, font_px=22)
