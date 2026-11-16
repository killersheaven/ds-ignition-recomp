"""Find switch jump tables in an unpacked Xbox 360 image (from xexdump) and write
a XenonRecomp switch TOML. base = address of the bctr, r = index register.
Usage: find_switches.py image.bin out.toml [image_base=0x82000000]"""
import struct, sys
img = open(sys.argv[1], 'rb').read()
IB = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x82000000
def rd(a, n):
    o = a - IB
    return int.from_bytes(img[o:o+n], 'big')
def rl(a, n):
    o = a - IB
    return int.from_bytes(img[o:o+n], 'little')
def s16(x): return x - 0x10000 if x & 0x8000 else x
M32 = 0xffffffff
def rotl(x, n): x &= M32; return ((x << n) | (x >> (32 - n))) & M32 if n else x
def mask(mb, me):
    m = 0
    for b in range(32):
        if (mb <= me and mb <= b <= me) or (mb > me and (b >= mb or b <= me)):
            m |= 1 << (31 - b)
    return m

# text range from PE section headers
pe = rl(IB + 0x3c, 4) + IB
nsec = rl(pe + 6, 2); opt = rl(pe + 20, 2); sh = pe + 24 + opt
texts = []
for i in range(nsec):
    s = sh + i * 40
    name = img[s - IB:s - IB + 8].rstrip(b'\0').decode(errors='replace')
    va, vs, ch = rl(s + 12, 4), rl(s + 8, 4), rl(s + 36, 4)
    if ch & 0x20: texts.append((name, IB + va, IB + va + vs))
# function bounds from .pdata (begin, packed len) for sanity checks
funcs = []
for name, a0, a1 in []: pass
pd = [ (rl(s+12,4)+IB, rl(s+8,4)) for s in [sh+i*40 for i in range(nsec)] if img[s-IB:s-IB+6]==b'.pdata' ]
if pd:
    a, n = pd[0]
    for o in range(a, a + n, 8):
        b = rd(o, 4); w = rd(o + 4, 4)
        if b: funcs.append((b, b + ((w >> 8) & 0x3fffff) * 4))
funcs.sort()
import bisect
fstarts = [f[0] for f in funcs]
def func_of(a):
    i = bisect.bisect_right(fstarts, a) - 1
    if i >= 0 and funcs[i][0] <= a < funcs[i][1]: return funcs[i]
    lo = funcs[i][1] if i >= 0 else a
    hi = funcs[i + 1][0] if i + 1 < len(funcs) else a + 4
    return (lo, hi)  # gap between pdata entries (leaf functions)


UNCOND = lambda w: (w >> 26) == 18 or w in (0x4E800020, 0x4E800420)  # b / blr / bctr

def evaluate(start, end, R0):
    """Linear concrete evaluation; returns (ctr, regs) or raises."""
    R = dict(R0); ctr = None; a = start
    def g(x): return R.get(x)
    def put(x, v):
        if v is None: R.pop(x, None)
        else: R[x] = v & M32
    while a < end:
        w = rd(a, 4); op = w >> 26; d = (w >> 21) & 31; A = (w >> 16) & 31; B = (w >> 11) & 31
        if op == 15: put(d, None if (A and g(A) is None) else (g(A) if A else 0) + (s16(w & 0xffff) << 16))
        elif op == 14: put(d, None if (A and g(A) is None) else (g(A) if A else 0) + s16(w & 0xffff))
        elif op == 7: put(d, None if g(A) is None else g(A) * s16(w & 0xffff))
        elif op == 24: put(A, None if g(d) is None else g(d) | (w & 0xffff))
        elif op == 21: put(A, None if g(d) is None else rotl(g(d), B) & mask((w >> 6) & 31, (w >> 1) & 31))
        elif op in (32, 34, 40, 42):
            base = 0 if A == 0 else g(A); sz = {32: 4, 34: 1, 40: 2, 42: 2}[op]
            put(d, None if base is None else rd((base + s16(w & 0xffff)) & M32, sz))
        elif op in (33, 35, 41, 43, 37, 39, 45, 47): put(A, None); put(d, None) if op in (33,35,41,43) else None
        elif op == 31:
            xo = (w >> 1) & 0x3ff
            if xo == 266: put(d, None if g(A) is None or g(B) is None else g(A) + g(B))
            elif xo in (23, 87, 279):
                sz = {23: 4, 87: 1, 279: 2}[xo]
                ea = None if (A and g(A) is None) or g(B) is None else (g(A) if A else 0) + g(B)
                put(d, None if ea is None else rd(ea & M32, sz))
            elif xo == 444: put(A, g(d) if d == B else None)
            elif xo == 467:
                if (A | (B << 5)) == 9: ctr = g(d)
            elif xo == 24: put(A, None if g(d) is None or g(B) is None else g(d) << (g(B) & 63))
            elif xo in (0, 32, 151, 215, 407, 150, 662, 918, 983, 86, 54, 278, 1014, 246, 470, 758): pass  # cmp/stores/cache ops
            else: put(d, None); put(A, None)
        elif op in (10, 11, 16, 19, 36, 38, 44, 46, 48, 49, 50, 51, 52, 53, 54, 55, 59, 63, 4, 60, 3, 2): pass  # cmp/branch/stores/fp/vmx
        else: put(d, None); put(A, None)
        a += 4
    return ctr, R

def analyse(bctr):
    f = func_of(bctr)
    if not f: return None, 'no function'
    # block start: after the last unconditional branch before bctr (max 64 insns)
    start = bctr
    while start > f[0] and bctr - start < 256 and not UNCOND(rd(start - 4, 4)): start -= 4
    # bounds check: cmplwi crN,rX,max followed by bgt/ble crN within window before bctr
    r = None; n = None; default = 0; cmpaddr = None
    for a in range(bctr - 4, max(f[0], bctr - 256) - 4, -4):
        w = rd(a, 4)
        if (w >> 26) == 10 and not (w >> 21) & 1:
            cr = (w >> 23) & 7
            for b2 in range(a + 4, min(a + 24, bctr), 4):
                x = rd(b2, 4)
                if (x >> 26) in (16, 19) and ((x >> 16) & 31) == cr * 4 + 1 and ((x >> 21) & 31) in (12, 4) and ((x >> 26) == 16 or ((x >> 1) & 0x3ff) == 16):
                    r = (w >> 16) & 31; n = (w & 0xffff) + 1; cmpaddr = a
                    if ((x >> 21) & 31) == 12 and (x >> 26) == 16: default = (b2 + s16(x & 0xfffc)) & M32
                    break
            if r is not None: break
    if cmpaddr is not None and cmpaddr >= start: start = cmpaddr  # evaluate from compare onwards
    # registers that are copies of the compared register (mr x,r / mr r,x) nearby
    copies = set()
    if r is not None:
        for a in range(max(f[0], bctr - 512), bctr, 4):
            w = rd(a, 4)
            if (w >> 26) == 31 and ((w >> 1) & 0x3ff) == 444 and ((w >> 21) & 31) == ((w >> 11) & 31):
                S, A = (w >> 21) & 31, (w >> 16) & 31
                if S == r: copies.add(A)
                if A == r: copies.add(S)
    trials = ([{r}] + [{r, c} for c in sorted(copies)]) if r is not None else [{x} for x in range(32)]
    for regs in trials:
        def run(i):
            try: return evaluate(start, bctr, {x: i for x in regs})
            except Exception: return None, {}
        probe = [run(i)[0] for i in range(n if n else 64)]
        if probe[0] is None or len(set(c for c in probe if c is not None)) < (1 if n else 2): continue
        # pick the register that still holds the index at the bctr
        _, R0 = run(0); _, R1 = run(1)
        live = [x for x in sorted(regs) if R0.get(x) == 0 and R1.get(x) == 1]
        if not live: return None, 'index reg clobbered'
        reg = live[0]
        labels = []
        for i in range(n if n else 1024):
            c = probe[i] if i < len(probe) else run(i)[0]
            if c is None or c & 3 or not (f[0] <= c < f[1]):
                if n: return None, 'bad label in bounded table'
                break
            labels.append(c)
        if not n and len(labels) < 2: continue
        return dict(base=bctr, r=reg, default=default, labels=labels, bounded=bool(n)), None
    return None, 'ctr not index-dependent (indirect call/tailcall)'

out = ['# Generated by find_switches.py (Dead Space Ignition)']
ok = bad = 0; reasons = {}; unb = []
for name, a0, a1 in texts:
    for a in range(a0, a1, 4):
        if rd(a, 4) != 0x4E800420: continue
        t, err = analyse(a)
        if t:
            f = func_of(a)
            outside = [l for l in t['labels'] if f and not (f[0] <= l < f[1])]
            if outside: err = 'labels outside function'; t = None
        if not t:
            bad += 1; reasons[err.split(' at ')[0]] = reasons.get(err.split(' at ')[0], 0) + 1
            print('skip %08x: %s' % (a, err), file=sys.stderr); continue
        ok += 1
        if not t['bounded']: unb.append(t['base'])
        out += ['[[switch]]', 'base = 0x%X' % t['base'], 'r = %d' % t['r'], 'default = 0x%X' % t['default'], 'labels = [']
        out += ['    0x%X,' % l for l in t['labels']] + [']', '']
open(sys.argv[2], 'w').write('\n'.join(out))
print('unbounded (sized by heuristic):', ' '.join('%X' % x for x in unb))
print('tables found:', ok, ' not tables / unresolved:', bad)
for k, v in sorted(reasons.items(), key=lambda x: -x[1]): print('  %4d %s' % (v, k))
