"""Build PS3 and keyboard button-prompt variants of Dead Space Ignition's UI files.

Usage: python3 make_button_mods.py <xbox SumoTool dir> <out dir> [<ps3 sumotool dir>]
Writes <out>/ps3_buttons/ and <out>/keyboard_buttons/ with subtitles_proj_EN.stz, popups_EN.stz and
Frontend_EN.stz. Without a PS3 folder the PlayStation symbols are drawn by ps3_glyphs.py; with one, the
PS3 version's own symbols are used instead.
Glyph mapping (follows the actual controls, not glyph positions):
  A->Cross/Space  B->Circle/Backspace  X->Square/L  Y->Triangle/P  LB->L1/1  RB->R1/3  LT->L2/Q  RT->R2/E
"""
import sys, os, zlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stz_export import streams, find_textures_ps3, decode_dxt
from stz_patch import load_texture, save_patched, paste_icon
from keyboard_glyphs import keycap, pill_key
import ps3_glyphs

XBOX_ORDER = ['RB', 'LB', 'RT', 'LT', 'Y', 'X', 'B', 'A']
PS3_ORDER = ['R1', 'L1', 'L2', 'R2', 'Square', 'Triangle', 'Circle', 'Cross']
PS3_MAP = {'RB': 'R1', 'LB': 'L1', 'RT': 'R2', 'LT': 'L2', 'Y': 'Triangle', 'X': 'Square', 'B': 'Circle', 'A': 'Cross'}
KEYS = {'A': ('', 'space'), 'B': ('', 'backspace'), 'X': ('L', None), 'Y': ('P', None),
        'LB': '1', 'RB': '3', 'LT': 'Q', 'RT': 'E'}

def components(mask):
    """Bounding boxes (x0, y0, x1, y1) of the 4-connected True regions of a 2-D mask, in order of
    first appearance (row-major), like scipy.ndimage.label + find_objects."""
    runs = []                                   # (row, start, stop) of every horizontal run
    for y in range(mask.shape[0]):
        row = np.concatenate(([0], mask[y].view(np.int8), [0]))
        d = np.flatnonzero(np.diff(row))
        runs += [(y, int(a), int(b)) for a, b in zip(d[::2], d[1::2])]
    parent = list(range(len(runs)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    prev, j0 = [], 0                            # link runs that overlap a run in the row above
    for i, (y, a, b) in enumerate(runs):
        if i and runs[i - 1][0] != y:
            prev = [k for k in range(j0, i) if runs[k][0] == y - 1]; j0 = i
        for k in prev:
            if runs[k][1] < b and a < runs[k][2]:
                ri, rk = find(i), find(k)
                if ri != rk: parent[max(ri, rk)] = min(ri, rk)
    boxes = {}
    for i, (y, a, b) in enumerate(runs):
        r = find(i)
        x0, y0, x1, y1 = boxes.get(r, (a, y, b, y + 1))
        boxes[r] = (min(x0, a), min(y0, y), max(x1, b), max(y1, y + 1))
    return [boxes[r] for r in sorted(boxes)]

def blobs(img, region, min_size=28):
    x0, y0, x1, y1 = region
    a = np.array(img)[y0:y1, x0:x1, 3]
    return [(bx0 + x0, by0 + y0, bx1 + x0, by1 + y0) for bx0, by0, bx1, by1 in components(a > 40)
            if bx1 - bx0 >= min_size and by1 - by0 >= min_size]

def font_icons(img):
    b = [r for r in blobs(img, (0, 0, img.width, img.height)) if r[1] < 60]
    b.sort(key=lambda r: (r[1] // 20, r[0]))
    return b[:8]

def ps3_texture(path, index):
    d = open(path, 'rb').read(); s = streams(d); cpu, gpu = s[0], s[-1]
    t = find_textures_ps3(cpu, len(gpu))[index]
    w, h = t['w'], t['h']; n = (w // 4) * (h // 4)
    blk = np.frombuffer(gpu[t['base']:t['base'] + n * 16], np.uint8).reshape(-1, 16)
    px = decode_dxt(blk, 3).reshape(h // 4, w // 4, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(h, w, 4)
    return Image.fromarray(np.ascontiguousarray(px))

def crop(img, box, pad=2):
    return img.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), box[2] + pad, box[3] + pad))

def kb_icon(name):
    v = KEYS[name]
    return pill_key(v) if name in ('LB', 'RB', 'LT', 'RT') else keycap(v[0], symbol=v[1])


# Menu file (Frontend_EN.stz): own copies of the prompts in three atlases.
FE_XBOX = {7: ('row', (1480, 1290, 1880, 1350), ['LB', 'Start', 'RB', 'X', 'B', 'Y', 'A']),
           0: ('big', [((1990, 860, 2048, 930), 'X'), ((1920, 1025, 2040, 1095), 'LB')]),
           1: ('big', [((1920, 1590, 2040, 1660), 'RB')])}
FE_PS3_ROW = (1480, 1290, 2010, 1350)
FE_PS3_ORDER = ['L1', 'R1', 'Start', 'Square', 'Triangle', 'Cross', 'Circle']
FE_PS3_MAP = dict(PS3_MAP, Start='Start')

def own_ps3(name, img, box, pad=2):
    """Self-drawn PS3 symbol for the Xbox cell `box` of `img` (name = Xbox button)."""
    w, h = box[2] - box[0], box[3] - box[1]
    p = FE_PS3_MAP[name]
    if p in ('L1', 'R1', 'L2', 'R2'):
        return ps3_glyphs.shoulder(crop(img, box, 0), p)
    if p == 'Start':
        return ps3_glyphs.start(w + 2 * pad - 2, h + 2 * pad - 2)
    return ps3_glyphs.face(p, min(w, h) + 2 * pad - 2)

def kb_icon_sized(name, box):
    w, h = box[2] - box[0], box[3] - box[1]
    if name in ('LB', 'RB', 'LT', 'RT'):
        return pill_key(KEYS[name])
    lab, sym = ('', 'enter') if name == 'Start' else KEYS[name]
    return keycap(lab, size=min(w, h) - 2, symbol=sym, font_px=15 * (min(w, h) - 2) / 31)

def frontend(xdir, pdir, out, variant):
    import tempfile, shutil
    src = os.path.join(xdir, 'Frontend_EN.stz')
    dst = os.path.join(out, variant, 'Frontend_EN.stz')
    tmp = dst + '.tmp'; shutil.copyfile(src, tmp)
    ps3 = pdir and os.path.join(pdir, 'frontend_en.stz')
    total = 0
    for idx, spec in FE_XBOX.items():
        img, ctx = load_texture(tmp, idx)
        if spec[0] == 'row':
            xb = sorted(blobs(img, spec[1], 24))[:7]
            pairs = list(zip(spec[2], xb))
            if variant == 'ps3_buttons' and pdir:
                pimg = ps3_texture(ps3, idx)
                pb = dict(zip(FE_PS3_ORDER, sorted(blobs(pimg, FE_PS3_ROW, 28))[:7]))
        else:
            pairs = [(name, sorted(blobs(img, reg, 24))[0]) for reg, name in spec[1]]
            if variant == 'ps3_buttons' and pdir:
                pimg = ps3_texture(ps3, idx)
                pb = {FE_PS3_MAP[name]: sorted(blobs(pimg, reg, 24))[0] for reg, name in spec[1]}
        for name, box in pairs:
            pad = 1 if spec[0] == 'row' else 2      # row icons sit 3-4 px apart, letters right after
            if variant == 'keyboard_buttons':
                icon = kb_icon_sized(name, box)
            elif pdir:
                icon = crop(pimg, pb[FE_PS3_MAP[name]], pad)
            else:
                icon = own_ps3(name, img, box, pad)
            paste_icon(img, box, icon, pad)
            print(f'    Frontend atlas {idx}: {name} {box}')
        total += save_patched(ctx, img, tmp)
    os.replace(tmp, dst)
    return total

def main(xdir, out, pdir=None):
    if pdir:
        ps3_font = ps3_texture(os.path.join(pdir, 'subtitles_proj_en.stz'), 0)
        ps3_pop = ps3_texture(os.path.join(pdir, 'popups_en.stz'), 1)
        p_icons = dict(zip(PS3_ORDER, font_icons(ps3_font)))
        p_pop = sorted(blobs(ps3_pop, (850, 0, 1024, 40), 24))        # [Square, Circle]
    for variant in ('ps3_buttons', 'keyboard_buttons'):
        os.makedirs(os.path.join(out, variant), exist_ok=True)
        # 1) subtitle font: all 8 button glyphs
        img, ctx = load_texture(os.path.join(xdir, 'subtitles_proj_EN.stz'), 0)
        x_icons = dict(zip(XBOX_ORDER, font_icons(img)))
        for name, box in x_icons.items():
            if variant == 'keyboard_buttons':
                icon = kb_icon(name)
            elif pdir:
                icon = crop(ps3_font, p_icons[PS3_MAP[name]])
            else:
                icon = own_ps3(name, img, box)
            paste_icon(img, box, icon)
        n1 = save_patched(ctx, img, os.path.join(out, variant, 'subtitles_proj_EN.stz'))
        img.save(os.path.join(out, variant, 'subtitles_proj_EN_preview.png'))
        # 2) pop-ups: A and B icons (third ring icon left as is)
        img, ctx = load_texture(os.path.join(xdir, 'popups_EN.stz'), 1)
        xa, xb = sorted(blobs(img, (850, 0, 1024, 40), 24))[:2]
        if variant == 'ps3_buttons' and not pdir:
            paste_icon(img, xa, own_ps3('A', img, xa)); paste_icon(img, xb, own_ps3('B', img, xb))
        elif variant == 'ps3_buttons':
            paste_icon(img, xa, crop(ps3_font, p_icons['Cross'])); paste_icon(img, xb, crop(ps3_pop, p_pop[1]))
        else:
            paste_icon(img, xa, kb_icon('A')); paste_icon(img, xb, kb_icon('B'))
        n2 = save_patched(ctx, img, os.path.join(out, variant, 'popups_EN.stz'))
        img.crop((840, 0, 1024, 40)).save(os.path.join(out, variant, 'popups_EN_preview.png'))
        n3 = frontend(xdir, pdir, out, variant)
        print(f'{variant}: subtitles {n1} blocks, popups {n2} blocks, frontend {n3} blocks')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
