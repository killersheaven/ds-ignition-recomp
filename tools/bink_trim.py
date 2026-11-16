"""Trim a Bink 1 (.bik) movie to its first N frames, producing a valid, very short movie.

Used to skip Dead Space Ignition's EA + Visceral logo movie (Resource/Movies/EaHd.bik): the game still
"plays" it, but it lasts a single frame, so no game logic changes.

Usage: python3 bink_trim.py <in.bik> <out.bik> [frames=1]

Bink 1 layout (little-endian): 'BIK?' | file_size-8 | num_frames | largest_frame | num_frames |
width | height | fps_num | fps_den | video_flags | num_audio_tracks | 12 bytes per audio track |
frame index: (num_frames+1) absolute offsets, bit 0 = keyframe | frame data.
"""
import sys, os, struct

def trim(src, dst, keep=1):
    d = open(src, 'rb').read()
    assert d[:3] == b'BIK', 'not a Bink 1 file'
    frames = struct.unpack('<I', d[8:12])[0]
    tracks = struct.unpack('<I', d[40:44])[0]
    keep = max(1, min(keep, frames))
    idx_at = 44 + tracks * 12
    idx = list(struct.unpack('<%dI' % (frames + 1), d[idx_at:idx_at + 4 * (frames + 1)]))
    assert (idx[0] & ~1) == idx_at + 4 * (frames + 1), 'unexpected frame index layout'
    start, end = idx[0] & ~1, idx[keep] & ~1
    data = d[start:end]
    shift = 4 * (frames - keep)                      # the index table gets shorter by this much
    new_idx = [((o & ~1) - shift) | (o & 1) for o in idx[:keep]] + [end - shift]
    largest = max((idx[i + 1] & ~1) - (idx[i] & ~1) for i in range(keep))
    hdr = bytearray(d[:idx_at])
    struct.pack_into('<I', hdr, 8, keep)
    struct.pack_into('<I', hdr, 12, largest)
    struct.pack_into('<I', hdr, 16, keep)
    out = bytes(hdr) + struct.pack('<%dI' % (keep + 1), *new_idx) + data
    out = out[:4] + struct.pack('<I', len(out) - 8) + out[8:]
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, 'wb').write(out)
    return frames, keep, len(d), len(out)

if __name__ == '__main__':
    f, k, a, b = trim(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1)
    print(f'{sys.argv[2]}: {f} -> {k} frames, {a} -> {b} bytes')
