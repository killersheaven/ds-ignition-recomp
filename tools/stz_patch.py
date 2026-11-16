"""Patch regions of a texture inside an Xbox 360 .stz (Dead Space Ignition / Sumo Digital UI file).

Library use:
    from stz_patch import load_texture, save_patched
    img, ctx = load_texture('popups_EN.stz', index=1)     # RGBA PIL image of texture #1
    ... edit img (paste icons etc.) ...
    save_patched(ctx, img, 'out.stz')                    # only changed DXT blocks are re-encoded

DXT1/3/5 and ARGB8888 Xenos textures (tiled, 8in16/8in32 endian) are supported.
"""
import sys, os, io, zlib, struct
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stz_export import streams, find_textures, untile_index, decode_dxt

KIND = {0x12: 1, 0x13: 3, 0x14: 5, 0x06: 'rgba'}

def build_stz(raw_streams):
    """.stz = 0x48-byte header of six (offset, raw size, compressed size) triples (unused ones = 0x48,0,0),
    then zlib streams, each starting 64-byte aligned relative to 0x48; file padded to 32 bytes."""
    out = bytearray(0x48); triples = []
    for raw in raw_streams:
        comp = zlib.compress(raw, 9)
        triples.append((len(out), len(raw), len(comp)))
        out += comp
        while (len(out) - 0x48) % 0x40: out += b'\0'
    while len(out) % 0x20: out += b'\0'
    words = [0x48, 0, 0] * (6 - len(triples))
    for t in triples: words += list(t)
    out[:0x48] = struct.pack('>18I', *words)
    return bytes(out)

def _swap(raw, endian):
    if endian == 1: return raw.reshape(-1, 2)[:, ::-1].reshape(-1)
    if endian == 2: return raw.reshape(-1, 4)[:, ::-1].reshape(-1)
    return raw

def load_texture(path, index):
    d = open(path, 'rb').read()
    s = streams(d)
    cpu, gpu = s[0], s[-1]
    t = find_textures(cpu, len(gpu))[index]
    kind = KIND[t['fmt']]
    bpp = 4 if kind == 'rgba' else 8 if kind == 1 else 16
    bp = 1 if kind == 'rgba' else 4
    wb, hb = t['w'] // bp, t['h'] // bp
    pb = max(wb, t['pitch'] // bp)
    size = ((pb + 31) & ~31) * ((hb + 31) & ~31) * bpp
    raw = _swap(np.frombuffer(gpu[t['base']:t['base'] + size], np.uint8), t['endian'])
    units = raw.reshape(-1, bpp).copy()
    ys, xs = np.mgrid[0:hb, 0:wb]
    tidx = untile_index(xs.astype(np.int64), ys.astype(np.int64), pb, bpp) if t['tiled'] else ys * pb + xs
    if kind == 'rgba':
        px = units[tidx.reshape(-1)].reshape(hb, wb, 4)[:, :, [1, 2, 3, 0]] if t['endian'] == 0 else units[tidx.reshape(-1)].reshape(hb, wb, 4)[:, :, [2, 1, 0, 3]]
    else:
        px = decode_dxt(units[tidx.reshape(-1)], kind).reshape(hb, wb, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(t['h'], t['w'], 4)
    img = Image.fromarray(np.ascontiguousarray(px))
    ctx = dict(streams=s, tex=t, kind=kind, bpp=bpp, bp=bp, wb=wb, hb=hb, tidx=tidx, units=units, size=size, orig=img.copy())
    return img, ctx

def save_patched(ctx, img, out_path):
    t, kind, bp, wb, hb = ctx['tex'], ctx['kind'], ctx['bp'], ctx['wb'], ctx['hb']
    img = img.convert('RGBA')
    diff = np.array(img, np.int16) != np.array(ctx['orig'], np.int16)
    units = ctx['units'].copy()
    if kind == 'rgba':
        changed = diff.any(axis=2)
        a = np.array(img)
        order = [3, 0, 1, 2] if t['endian'] == 0 else [2, 1, 0, 3]
        for y, x in zip(*np.nonzero(changed)):
            units[ctx['tidx'][y, x]] = a[y, x][order]
        n = int(changed.sum())
    else:
        changed = diff.reshape(hb, 4, wb, 4, 4).any(axis=(1, 3, 4))
        buf = io.BytesIO(); img.save(buf, 'DDS', pixel_format={1: 'DXT1', 3: 'DXT3', 5: 'DXT5'}[kind])
        dds = buf.getvalue(); bpp = ctx['bpp']
        newblk = np.frombuffer(dds[128:128 + wb * hb * bpp], np.uint8).reshape(hb, wb, bpp)
        for by, bx in zip(*np.nonzero(changed)):
            units[ctx['tidx'][by, bx]] = newblk[by, bx]
        n = int(changed.sum())
    raw = _swap(units.reshape(-1), t['endian']).tobytes()
    gpu = bytearray(ctx['streams'][-1]); gpu[t['base']:t['base'] + len(raw)] = raw
    out = build_stz(ctx['streams'][:-1] + [bytes(gpu)])
    open(out_path, 'wb').write(out)
    return n

def paste_icon(img, box, icon, pad=2):
    """Clear the glyph cell `box` (x0,y0,x1,y1, plus `pad`) and centre `icon` (RGBA) in it."""
    x0, y0, x1, y1 = box
    cx0, cy0, cx1, cy1 = max(x0 - pad, 0), max(y0 - pad, 0), x1 + pad, y1 + pad
    img.paste((0, 0, 0, 0), (cx0, cy0, cx1, cy1))
    cw, ch = cx1 - cx0, cy1 - cy0
    if icon.width > cw or icon.height > ch:
        icon = icon.resize((min(icon.width, cw), min(icon.height, ch)), Image.LANCZOS)
    img.alpha_composite(icon, (cx0 + (cw - icon.width) // 2, cy0 + (ch - icon.height) // 2))
