#!/usr/bin/env python3
"""Minimal STFS (LIVE/PIRS/CON) extractor. Usage: stfs_extract.py <package> <outdir> [--list]
Resumable: skips files already present with the right size."""
import sys, os, struct, time

def extract(pkg, out, list_only=False, log=print):
    """Extract every file of STFS package `pkg` into `out`; returns the number of files."""
    f = open(pkg, 'rb')
    hdr = f.read(0x971A)
    magic = hdr[:4]
    if magic not in (b'LIVE', b'PIRS', b'CON '):
        raise ValueError(f'{pkg} is not an Xbox 360 package (STFS)')
    header_size = struct.unpack('>I', hdr[0x340:0x344])[0]
    vd = hdr[0x379:0x379+0x24]
    block_sep = vd[2]
    ft_count = struct.unpack('<H', vd[3:5])[0]
    ft_block = int.from_bytes(vd[5:8], 'little')
    total_alloc = struct.unpack('>I', vd[0x1C:0x20])[0]
    sex = (~block_sep) & 1
    first_ht = (header_size + 0xFFF) & 0xFFFFF000
    log(f"magic={magic} header_size={header_size:#x} block_sep={block_sep} sex={sex} first_ht={first_ht:#x} ft_block={ft_block} ft_count={ft_count} total_alloc={total_alloc}")
    step0 = 0xAB if sex == 0 else 0xAC

    def data_addr(b):
        r = (((b + 0xAA) // 0xAA) << sex) + b
        if b >= 0xAA:
            r += ((b + 0x70E4) // 0x70E4) << sex
            if b >= 0x70E4:
                r += 1 << sex
        return (r << 12) + first_ht

    def l0_addr(b):
        if b < 0xAA:
            n = 0
        else:
            n = (b // 0xAA) * step0
            n += ((b // 0x70E4) + 1) << sex
            if b // 0x70E4 != 0:
                n += 1 << sex
        return (n << 12) + first_ht

    htcache = {}
    def next_block(b):
        a = l0_addr(b)
        if a not in htcache:
            if len(htcache) > 64: htcache.clear()
            f.seek(a); t0 = f.read(0x1000)
            if sex == 1:
                f.seek(a + 0x1000); t1 = f.read(0x1000)
                htcache[a] = (t0, t1)
            else:
                htcache[a] = (t0, None)
        t0, t1 = htcache[a]
        i = (b % 0xAA) * 0x18
        e = t0[i:i+0x18]
        if t1 is not None and e[0x14] & 0x80 == 0 and t1[i+0x14] & 0x80:
            e = t1[i:i+0x18]
        return int.from_bytes(e[0x15:0x18], 'big')

    def read_block(b):
        f.seek(data_addr(b)); return f.read(0x1000)

    # file table
    tbl = b''
    b = ft_block
    for _ in range(ft_count):
        tbl += read_block(b)
        b = next_block(b)
    entries = []
    for i in range(0, len(tbl), 0x40):
        e = tbl[i:i+0x40]
        if e[0] == 0: break
        fl = e[0x28]
        name = e[:fl & 0x3F].decode('latin-1')
        entries.append(dict(name=name, dir=bool(fl & 0x80), consec=bool(fl & 0x40),
            blocks=int.from_bytes(e[0x29:0x2C], 'little'),
            start=int.from_bytes(e[0x2F:0x32], 'little'),
            parent=struct.unpack('>H', e[0x32:0x34])[0],
            size=struct.unpack('>I', e[0x34:0x38])[0],
            ts=struct.unpack('>I', e[0x38:0x3C])[0]))
    def path(i):
        e = entries[i]
        return e['name'] if e['parent'] == 0xFFFF else path(e['parent']) + '/' + e['name']
    t_start = time.time()
    for i, e in enumerate(entries):
        p = path(i)
        if list_only:
            log(f"{'D' if e['dir'] else 'F'} {e['size']:>12} blk={e['start']:<8} n={e['blocks']:<7} c={int(e['consec'])} ts={e['ts']:#010x} {p}")
            continue
        op = os.path.join(out, p)
        if e['dir']:
            os.makedirs(op, exist_ok=True); continue
        os.makedirs(os.path.dirname(op) or '.', exist_ok=True)
        if os.path.exists(op) and os.path.getsize(op) == e['size']:
            continue
        tmp = op + '.part'
        with open(tmp, 'wb') as o:
            left = e['size']; b = e['start']
            while left > 0:
                d = read_block(b)
                o.write(d[:min(left, 0x1000)])
                left -= 0x1000
                b = b + 1 if e['consec'] else next_block(b)
        os.replace(tmp, op)
        log(f"ok {e['size']:>12} {p}  ({time.time()-t_start:.0f}s)")
    log("DONE")
    return sum(1 for e in entries if not e['dir'])

if __name__ == '__main__':
    extract(sys.argv[1], sys.argv[2], '--list' in sys.argv)
