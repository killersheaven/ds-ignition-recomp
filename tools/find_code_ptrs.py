"""Find code addresses built with lis/addi (or lis/ori) that are not registered
function starts in ReXGlue's generated register file. Usage: image.bin register.cpp"""
import struct, re, sys
d = open(sys.argv[1], 'rb').read(); IB = 0x82000000
T0, T1 = 0x82110000, 0x824F2B70
reg = set(int(x, 16) for x in re.findall(r'SetFunction\(0x([0-9A-F]+)', open(sys.argv[2]).read()))
rd = lambda a: struct.unpack('>I', d[a-IB:a-IB+4])[0]
def s16(x): return x - 0x10000 if x & 0x8000 else x
cands = {}
for a in range(T0, T1, 4):
    w = rd(a)
    if w >> 26 == 15 and ((w >> 16) & 31) == 0:      # lis rD, hi
        rD = (w >> 21) & 31; hi = (w & 0xffff) << 16
        for k in range(1, 12):
            b = a + 4 * k; x = rd(b); op = x >> 26
            if op in (14, 24) and ((x >> 16) & 31 if op == 14 else (x >> 21) & 31) == rD:
                lo = s16(x & 0xffff) if op == 14 else (x & 0xffff)
                tgt = (hi + lo) & 0xffffffff
                if T0 <= tgt < T1 and tgt % 4 == 0 and tgt not in reg:
                    cands.setdefault(tgt, []).append(b)
                break
            if (x >> 21) & 31 == rD and op not in (36, 37, 38, 44, 32):  # rD overwritten
                break
def plausible(t):
    p = rd(t - 4)
    return p in (0x4E800020, 0) or (p >> 26) == 18   # after blr / padding / unconditional b
good = sorted(t for t in cands if plausible(t))
print('computed code addresses not registered:', len(cands), ' plausible function starts:', len(good))
for t in good: print('0x%08X refs %s' % (t, ' '.join('%X' % r for r in cands[t][:3])))
