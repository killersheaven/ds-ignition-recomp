"""PS3 / keyboard button prompts for Dead Space Ignition's hacking minigames.

Hardware Crack and Software Hack draw their prompts from 2x2 ring textures inside their asset sets
(<Set>.zif = zlib'd engine data with the texture table, <Set>.zig = zlib'd GPU data):
    Xbox rings (bright, dim)   PS3 rings (bright, dim)   -- the PS3 ones already ship in the Xbox files
    HardwareCrack: 25, 28       29, 30
    SoftwareHack:  85, 88       89, 91
Quadrants: Xbox X Y / A B, PS3 Triangle Circle / Square Cross.  Mapping by control:
    X->Square  Y->Triangle  A->Cross  B->Circle   (keyboard: X=L  Y=P  A=Space  B=Backspace)
Only the top mip level is rewritten, so the texture's mip range is limited to level 0 (fetch dword 4),
otherwise the untouched Xbox mips would show at a distance.

Usage: python3 minigame_buttons.py <Resource dir with originals> <out dir>
Writes <out>/ps3_buttons/<Set>.zif/.zig and <out>/keyboard_buttons/<Set>.zif/.zig
"""
import sys, os, io, zlib, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stz_export import untile_index, decode_dxt

SETS = {'HardwareCrack/HardwareCrackSet': {25: 29, 28: 30},
        'SoftwareHack/SoftwareHackSet':   {85: 89, 88: 91}}
# quadrant index: 0=TL 1=TR 2=BL 3=BR.  Xbox: X Y A B   PS3: Tri Circ Sq Cross
XBOX_Q = {'X': 0, 'Y': 1, 'A': 2, 'B': 3}
PS3_Q = {'Triangle': 0, 'Circle': 1, 'Square': 2, 'Cross': 3}
PS3_FOR = {'X': 'Square', 'Y': 'Triangle', 'A': 'Cross', 'B': 'Circle'}
KEY_FOR = {'X': 'L', 'Y': 'P', 'A': 'space', 'B': 'backspace'}
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'DejaVuSans-Bold.ttf')   # bundled: same output on every OS

def unz(path):
    d = zlib.decompress(open(path, 'rb').read())
    return d[:4], bytearray(d[4:])

def rez(prefix, data):
    return zlib.compress(bytes(prefix) + bytes(data), 9)

def table(cpu):
    """60-byte texture records: fetch constant at +0x24, GPU base in the first word of the next record."""
    best = []
    for o in range(0, len(cpu) - 0x80, 4):
        f0 = struct.unpack('>I', cpu[o + 0x24:o + 0x28])[0]
        g0 = struct.unpack('>I', cpu[o + 0x60:o + 0x64])[0]
        if f0 & 3 != 2 or not f0 >> 31 or g0 & 3 != 2 or not g0 >> 31: continue
        run = []; r = o
        while r + 0x40 <= len(cpu):
            a0 = struct.unpack('>I', cpu[r + 0x24:r + 0x28])[0]
            if a0 & 3 != 2 or not a0 >> 31: break
            run.append(r); r += 0x3c
        if len(run) > len(best): best = run
    out = []
    for r in best:
        f = r + 0x24
        f0, f1, f2 = struct.unpack('>3I', cpu[f:f + 12])
        out.append(dict(fetch=f, fmt=f1 & 0x3f, w=(f2 & 0x1fff) + 1, h=((f2 >> 13) & 0x1fff) + 1,
                        pitch=((f0 >> 22) & 0x1ff) * 32, base=struct.unpack('>I', cpu[f + 0x18:f + 0x1c])[0]))
    return out

def _layout(t):
    assert t['fmt'] == 0x14, 'expects DXT5'
    wb, hb = t['w'] // 4, t['h'] // 4; pb = max(wb, t['pitch'] // 4)
    ys, xs = np.mgrid[0:hb, 0:wb]
    return wb, hb, untile_index(xs.astype(np.int64), ys.astype(np.int64), pb, 16)

def read_tex(gpu, t):
    wb, hb, idx = _layout(t)
    raw = np.frombuffer(bytes(gpu[t['base']:t['base'] + wb * hb * 16 * 4]), np.uint8)
    blk = raw.reshape(-1, 2)[:, ::-1].reshape(-1, 16)          # 8in16 -> little-endian DXT
    px = decode_dxt(blk[idx.reshape(-1)], 5).reshape(hb, wb, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(t['h'], t['w'], 4)
    return Image.fromarray(np.ascontiguousarray(px))

def write_tex(gpu, cpu, t, img):
    wb, hb, idx = _layout(t)
    buf = io.BytesIO(); img.convert('RGBA').save(buf, 'DDS', pixel_format='DXT5')
    new = np.frombuffer(buf.getvalue()[128:128 + wb * hb * 16], np.uint8).reshape(hb, wb, 16)
    raw = np.frombuffer(bytes(gpu[t['base']:t['base'] + wb * hb * 16 * 4]), np.uint8).reshape(-1, 2)[:, ::-1].reshape(-1, 16).copy()
    raw[idx] = new
    out = raw.reshape(-1, 2)[:, ::-1].reshape(-1).tobytes()
    gpu[t['base']:t['base'] + len(out)] = out
    # limit the mip range to level 0 (dword 4 bits 6-9 = max level), so the old mips are never sampled
    o = t['fetch'] + 16
    d4 = struct.unpack('>I', cpu[o:o + 4])[0] & ~(0xf << 6)
    cpu[o:o + 4] = struct.pack('>I', d4)

def quad(img, q):
    s = img.width // 2
    return (q % 2) * s, (q // 2) * s, (q % 2) * s + s, (q // 2) * s + s

def ps3_image(xbox, ps3):
    out = xbox.copy()
    for name, q in XBOX_Q.items():
        out.paste(ps3.crop(quad(ps3, PS3_Q[PS3_FOR[name]])), quad(out, q)[:2])
    return out

def keyboard_quadrant(cell, label, clean=None):
    """Clear the inside of the ring (it is transparent apart from the symbol) and draw the key label the way
    the PS3 symbols are drawn: solid stroke in the ring's band colour, with the ring's bright edge colour as outline.
    Geometry from the 128 px quadrant: outer ring band r = 52..58, transparent gap r = 42..49."""
    # `clean`: a PS3 Circle quadrant from the same texture family - identical outer ring, no old letter tips
    a = np.array((clean or cell).convert('RGBA')).astype(np.float32)
    n = a.shape[0]; k = n / 128.0
    yy, xx = np.mgrid[0:n, 0:n]; r = np.hypot(xx - (n - 1) / 2, yy - (n - 1) / 2)
    band = a[(r >= 53 * k) & (r <= 57 * k)]
    ink = np.median(band[band[:, 3] > 200][:, :3], 0)
    rim = a[(r >= 60 * k) & (r <= 62 * k)]
    edge = np.median(rim[rim[:, 3] > 100][:, :3], 0)
    clear = r < 49.5 * k
    a[clear, 3] = 0; a[clear, :3] = edge          # transparent, colour like the existing gap pixels
    base = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    S = 4; N = n * S; c = N / 2
    big = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    col = tuple(int(v) for v in ink) + (255,); out = tuple(int(v) for v in edge) + (255,)
    w = int(5.5 * k * S); ow = int(2.0 * k * S)
    def stroke_line(pts, **kw):
        d.line(pts, fill=out, width=w + 2 * ow, joint='curve'); d.line(pts, fill=col, width=w, joint='curve')
    if label == 'space':
        bw, bh = 52 * k * S, 16 * k * S
        x0, y0 = c - bw / 2, c - bh / 2 + 4 * k * S
        stroke_line((x0, y0, x0, y0 + bh, x0 + bw, y0 + bh, x0 + bw, y0))
    elif label == 'backspace':
        bw, bh = 56 * k * S, 36 * k * S
        x0, y0 = c - bw / 2, c - bh / 2
        pts = [(x0, c), (x0 + 0.33 * bh, y0), (x0 + bw, y0), (x0 + bw, y0 + bh), (x0 + 0.33 * bh, y0 + bh), (x0, c)]
        stroke_line(pts)
        m = 8 * k * S; ox = x0 + 0.62 * bw
        stroke_line((ox - m, c - m, ox + m, c + m)); stroke_line((ox - m, c + m, ox + m, c - m))
    else:
        f = ImageFont.truetype(FONT, int(62 * k * S))
        d.text((c, c + 2 * k * S), label, font=f, fill=col, anchor='mm', stroke_width=ow, stroke_fill=out)
    lab = big.resize((n, n), Image.LANCZOS)
    return Image.alpha_composite(base, lab)

def keyboard_image(xbox, ps3=None):
    out = xbox.copy()
    clean = ps3.crop(quad(ps3, PS3_Q['Circle'])) if ps3 is not None else None
    for name, q in XBOX_Q.items():
        box = quad(out, q)
        out.paste(keyboard_quadrant(out.crop(box), KEY_FOR[name], clean), box[:2])
    return out

def build(src_dir, out_dir):
    for set_name, pairs in SETS.items():
        pre_c, cpu0 = unz(os.path.join(src_dir, set_name + '.zif'))
        pre_g, gpu0 = unz(os.path.join(src_dir, set_name + '.zig'))
        ts = table(cpu0)
        for variant in ('ps3_buttons', 'keyboard_buttons'):
            cpu, gpu = bytearray(cpu0), bytearray(gpu0)
            for xi, pi in pairs.items():
                xb = read_tex(gpu0, ts[xi])
                ps = read_tex(gpu0, ts[pi])
                img = ps3_image(xb, ps) if variant == 'ps3_buttons' else keyboard_image(xb, ps)
                write_tex(gpu, cpu, ts[xi], img)
                pv = os.path.join(out_dir, variant, 'preview'); os.makedirs(pv, exist_ok=True)
                img.save(os.path.join(pv, f'{os.path.basename(set_name)}_{xi}.png'))
            d = os.path.join(out_dir, variant, os.path.dirname(set_name)); os.makedirs(d, exist_ok=True)
            open(os.path.join(d, os.path.basename(set_name) + '.zif'), 'wb').write(rez(pre_c, cpu))
            open(os.path.join(d, os.path.basename(set_name) + '.zig'), 'wb').write(rez(pre_g, gpu))
            print(f'{variant}: {set_name} textures {list(pairs)} rewritten')

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
