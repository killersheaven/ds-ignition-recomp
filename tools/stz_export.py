"""Export textures from a Sumo Digital .stz (SumoTool UI) file - Xbox 360 version.
Usage: python3 stz_export.py <file.stz> <out_dir>
Format notes: 0x48-byte header of stream offsets, then 3 zlib streams
(CPU data, RELO tables, GPU data). Textures are Xenos fetch constants inside the
CPU data; pixel data is in the GPU stream (tiled, 8in16 endian)."""
import sys, os, zlib, struct
import numpy as np
from PIL import Image

def streams(d):
    out = []; o = 0x48
    while o < len(d):
        z = zlib.decompressobj(); s = z.decompress(d[o:]); out.append(s)
        o = len(d) - len(z.unused_data)
        while o < len(d) and d[o] != 0x78: o += 1
    return out

def parse_fetch(cpu, o, base):
    f0, f1, f2 = struct.unpack('>III', cpu[o:o+12])
    if f0 & 3 != 2: return None
    w = (f2 & 0x1fff) + 1; h = ((f2 >> 13) & 0x1fff) + 1
    return dict(at=o, fmt=f1 & 0x3f, endian=(f1 >> 6) & 3, tiled=f0 >> 31, base=base,
                pitch=((f0 >> 22) & 0x1ff) * 32, w=w, h=h)

def find_textures(cpu, gpu_len):
    """Texture index: 'count' then (gpu_offset, record_ptr) pairs; fetch constant at record+0x2C.
    The index location is found by searching for a run of pairs whose record pointers are 0x34 apart."""
    best = []; best_at = 0
    for o in range(0, len(cpu) - 16, 4):
        g0, r0, g1, r1 = struct.unpack('>IIII', cpu[o:o+16])
        if r1 - r0 != 0x34 or g0 >= gpu_len or g1 <= g0 or g1 >= gpu_len or r0 >= len(cpu): continue
        pairs = []; k = o
        while k + 8 <= len(cpu):
            g, r = struct.unpack('>II', cpu[k:k+8])
            if pairs and (r - pairs[-1][1] != 0x34 or g < pairs[-1][0] or g >= gpu_len): break
            pairs.append((g, r)); k += 8
        if len(pairs) > len(best): best, best_at = pairs, o
    # Each entry is really (record_ptr, gpu_offset): the record for gpu_offset g[i] is the
    # pointer stored just before it, so shift by one and take the record from the word before the run.
    tex = []
    if best:
        first = struct.unpack('>I', cpu[best_at - 4:best_at])[0]
        recs = [first] + [r for _, r in best]
        tail = best_at + 8 * len(best)
        gs = [g for g, _ in best]
        if tail + 4 <= len(cpu):
            g_last = struct.unpack('>I', cpu[tail:tail+4])[0]
            if gs and gs[-1] < g_last < gpu_len: gs.append(g_last)
        for r, g in zip(recs, gs):
            t = parse_fetch(cpu, r + 0x2c, g)
            if t: tex.append(t)
    if not tex:
        # single-texture files have no index run: scan for one plausible fetch constant at GPU offset 0
        for o in range(0, len(cpu) - 12, 4):
            t = parse_fetch(cpu, o, 0)
            if not t or t['fmt'] not in (0x06, 0x12, 0x13, 0x14) or t['endian'] not in (1, 2): continue
            if not (t['tiled'] and 16 <= t['w'] <= 4096 and 16 <= t['h'] <= 4096 and t['pitch'] >= t['w']): continue
            bpp = 4 if t['fmt'] == 6 else 8 if t['fmt'] == 0x12 else 16
            bp = 1 if t['fmt'] == 6 else 4
            need = ((t['pitch'] // bp + 31) & ~31) * ((t['h'] // bp + 31) & ~31) * bpp
            if need <= gpu_len:
                tex.append(t); break
    return tex

def untile_index(x, y, w_blocks, bpp):
    aligned = (w_blocks + 31) & ~31
    log_bpp = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}[bpp]
    macro = ((x >> 5) + (y >> 5) * (aligned >> 5)) << (log_bpp + 7)
    micro = ((x & 7) + ((y & 6) << 2)) << log_bpp
    off = macro + ((micro & ~15) << 1) + (micro & 15) + ((y & 8) << (3 + log_bpp)) + ((y & 1) << 4)
    return (((off & ~511) << 3) + ((off & 448) << 2) + (off & 63) + ((y & 16) << 7)
            + (((((y & 8) >> 2) + (x >> 3)) & 3) << 6)) >> log_bpp

def decode_dxt(blocks, kind):
    """blocks: (N,16) uint8 little-endian DXT3/DXT5 blocks (or (N,8) DXT1). Returns (N,4,4,4) RGBA."""
    n = len(blocks)
    cb = blocks[:, -8:]
    c0 = cb[:, 0].astype(np.uint32) | (cb[:, 1].astype(np.uint32) << 8)
    c1 = cb[:, 2].astype(np.uint32) | (cb[:, 3].astype(np.uint32) << 8)
    def rgb(c):
        return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], -1)
    p0, p1 = rgb(c0), rgb(c1)
    four = (c0 > c1) | (kind != 1)
    p2 = np.where(four[:, None], (2 * p0 + p1) // 3, (p0 + p1) // 2)
    p3 = np.where(four[:, None], (p0 + 2 * p1) // 3, 0)
    pal = np.stack([p0, p1, p2, p3], 1)  # (N,4,3)
    idx = (cb[:, 4].astype(np.uint32) | (cb[:, 5].astype(np.uint32) << 8) | (cb[:, 6].astype(np.uint32) << 16) | (cb[:, 7].astype(np.uint32) << 24))
    sel = np.stack([(idx >> (2 * i)) & 3 for i in range(16)], 1)  # (N,16)
    col = np.take_along_axis(pal, sel[:, :, None].repeat(3, 2), 1)  # (N,16,3)
    if kind == 3:
        a = blocks[:, :8]
        al = np.stack([(a[:, i // 2] >> (4 * (i & 1))) & 15 for i in range(16)], 1) * 17
    elif kind == 5:
        a0 = blocks[:, 0].astype(np.int32); a1 = blocks[:, 1].astype(np.int32)
        bits = sum(blocks[:, 2 + i].astype(np.uint64) << np.uint64(8 * i) for i in range(6))
        ai = np.stack([((bits >> np.uint64(3 * i)) & np.uint64(7)).astype(np.int32) for i in range(16)], 1)
        tab8 = [a0, a1] + [((7 - k) * a0 + k * a1) // 7 for k in range(1, 7)]
        tab6 = [a0, a1] + [((5 - k) * a0 + k * a1) // 5 for k in range(1, 5)] + [np.zeros_like(a0), np.full_like(a0, 255)]
        tab = np.where((a0 > a1)[:, None], np.stack(tab8, 1), np.stack(tab6, 1))
        al = np.take_along_axis(tab, ai, 1)
    else:
        al = np.where((~four)[:, None] & (sel == 3), 0, 255)
    rgba = np.concatenate([col, al[:, :, None]], 2).astype(np.uint8)
    return rgba.reshape(n, 4, 4, 4)


def find_textures_ps3(cpu, gpu_len):
    """PS3 (RSX) records: CellGcmTexture {u8 format, mipmap, dimension(2), cubemap; u32 remap; u16 w, h, depth;
    u8 location, pad; u32 pitch, offset}. Each record is referenced by a (record_offset - 0x10, gpu_offset) pair."""
    tex = []
    for o in range(0x10, len(cpu) - 24, 4):
        fmt, mip, dim, cube = cpu[o:o+4]
        if dim != 2 or cube != 0 or struct.unpack('>I', cpu[o+4:o+8])[0] != 0x0000aae4: continue
        w, h, depth = struct.unpack('>HHH', cpu[o+8:o+14])
        pitch = struct.unpack('>I', cpu[o+16:o+20])[0]
        ref = struct.pack('>I', o - 0x10); k = cpu.find(ref)
        base = struct.unpack('>I', cpu[k+4:k+8])[0] if 0 <= k < o else 0
        base_fmt = fmt & 0x9f
        kind = {0x86: 1, 0x87: 3, 0x88: 5, 0x85: 'rgba'}.get(base_fmt)
        tex.append(dict(at=o, fmt=fmt, kind=kind, linear=bool(fmt & 0x40), w=w, h=h, pitch=pitch, base=base))
    return tex

def export_ps3(path, cpu, gpu, out_dir):
    texs = find_textures_ps3(cpu, len(gpu))
    print(f'{os.path.basename(path)} (PS3): GPU {len(gpu)} bytes, {len(texs)} textures')
    for i, t in enumerate(texs):
        if t['kind'] is None or not t['linear']:
            print('  skip', hex(t['fmt']), 'linear' if t['linear'] else 'swizzled'); continue
        w, h = t['w'], t['h']
        if t['kind'] == 'rgba':
            pitch = t['pitch'] or w * 4
            a = np.frombuffer(gpu[t['base']:t['base'] + pitch * h], np.uint8).reshape(h, pitch)[:, :w * 4].reshape(h, w, 4)
            px = a[:, :, [1, 2, 3, 0]]                      # ARGB (big-endian) -> RGBA
            tag = 'argb8888'
        else:
            bpp = 8 if t['kind'] == 1 else 16
            n = (w // 4) * (h // 4)
            blk = np.frombuffer(gpu[t['base']:t['base'] + n * bpp], np.uint8).reshape(-1, bpp)
            px = decode_dxt(blk, t['kind']).reshape(h // 4, w // 4, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(h, w, 4)
            tag = f"dxt{t['kind']}"
        name = f"{os.path.splitext(os.path.basename(path))[0]}_ps3_{i:02d}_{w}x{h}_{tag}.png"
        Image.fromarray(np.ascontiguousarray(px)).save(os.path.join(out_dir, name))
        print('  ', name, 'base', hex(t['base']))

def export(path, out_dir):
    d = open(path, 'rb').read()
    s = streams(d)
    cpu, gpu = s[0], s[-1]
    os.makedirs(out_dir, exist_ok=True)
    if find_textures_ps3(cpu, len(gpu)):
        return export_ps3(path, cpu, gpu, out_dir)
    texs = find_textures(cpu, len(gpu))
    print(f'{os.path.basename(path)}: {len(s)} streams, GPU {len(gpu)} bytes, {len(texs)} textures')
    for i, t in enumerate(texs):
        kind = {0x12: 1, 0x13: 3, 0x14: 5, 0x06: 'rgba'}.get(t['fmt'])
        if kind is None:
            print('  skip fmt', hex(t['fmt'])); continue
        bpp = 4 if kind == 'rgba' else 8 if kind == 1 else 16
        blk_px = 1 if kind == 'rgba' else 4
        wb, hb = (t['w'] + blk_px - 1) // blk_px, (t['h'] + blk_px - 1) // blk_px
        pb = max(wb, (t['pitch'] or t['w']) // blk_px)
        size = ((pb + 31) & ~31) * ((hb + 31) & ~31) * bpp
        raw = np.frombuffer(gpu[t['base']:t['base'] + size], np.uint8)
        if len(raw) < size: print('  short data for', i); continue
        if t['endian'] == 1: raw = raw.reshape(-1, 2)[:, ::-1].reshape(-1)       # 8in16
        elif t['endian'] == 2: raw = raw.reshape(-1, 4)[:, ::-1].reshape(-1)     # 8in32
        blocks_all = raw.reshape(-1, bpp)
        ys, xs = np.mgrid[0:hb, 0:wb]
        if t['tiled']:
            idx = untile_index(xs.astype(np.int64), ys.astype(np.int64), pb, bpp)
        else:
            idx = ys * pb + xs
        blk = blocks_all[idx.reshape(-1)]
        if kind == 'rgba':
            argb = blk.reshape(hb, wb, 4)        # stored big-endian ARGB after endian swap
            px = argb[:, :, [1, 2, 3, 0]] if t['endian'] == 0 else argb[:, :, [2, 1, 0, 3]]
            tag = 'argb8888'
        else:
            px = decode_dxt(blk, kind).reshape(hb, wb, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(hb * 4, wb * 4, 4)
            tag = f'dxt{kind}'
        name = f"{os.path.splitext(os.path.basename(path))[0]}_{i:02d}_{t['w']}x{t['h']}_{tag}.png"
        Image.fromarray(px[:t['h'], :t['w']]).save(os.path.join(out_dir, name))
        print('  ', name, 'base', hex(t['base']))

if __name__ == '__main__':
    export(sys.argv[1], sys.argv[2])
