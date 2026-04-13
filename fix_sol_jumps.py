#!/usr/bin/env python3
"""
Fix s.sol jump section: replace sentinel-corrupted jump data with clean entries,
and remove stale bytes between ball and view sections.

The pre-compiled s.sol has jc=8 but only 6 actual jump entries in the file.
Seven sentinel pairs (0xFFFFFFFF x2) fill the remaining space, displacing
entries 6 and 7.  The correct positions for those entries come from the MAP
source (target_teleporter entities).
"""

import struct, os, sys, shutil

SOL_VERSION_1_6 = 7
M_ALPHA_TEST = 1 << 9
P_ORIENTED = 1
PATHMAX = 64

# All 8 jump entries — first 6 from the SOL file, last 2 from s.map
JUMPS = [
    # p=(x, y, z),               q=(x, y, z),           r
    ((  3.375, 0.25, -3.625), (5.0, 0.25, 1.0), 0.5),
    ((  0.500, 0.25, -4.500), (5.0, 0.25, 1.0), 0.5),
    (( -1.375, 0.25, -5.250), (5.0, 0.25, 1.0), 0.5),
    (( -3.625, 0.25, -2.875), (5.0, 0.25, 1.0), 0.5),
    (( -5.875, 0.25,  2.125), (5.0, 0.25, 1.0), 0.5),
    (( -6.625, 0.25,  4.250), (5.0, 0.25, 1.0), 0.5),
    ((-10.750, 0.25,  4.750), (5.0, 0.25, 1.0), 0.5),  # from MAP
    ((-14.500, 0.25,  1.750), (5.0, 0.25, 1.0), 0.5),  # from MAP
]

def read_int(f):
    return struct.unpack('<i', f.read(4))[0]

def skip_to_jump_section(f):
    """Skip to the jump section, returning (jump_offset, counts dict).
    Uses the same parsing logic as fix_sol_balls.py."""

    magic = read_int(f)
    version = read_int(f)

    expected_magic = 0xAF | (ord('S') << 8) | (ord('O') << 16) | (ord('L') << 24)
    assert magic == expected_magic, f"Bad magic: 0x{magic:08X}"
    assert version == 9, f"Expected version 9, got {version}"

    ac = read_int(f)
    dc = read_int(f)
    mc = read_int(f)
    vc = read_int(f)
    ec = read_int(f)
    sc = read_int(f)
    tc = read_int(f)
    oc = read_int(f) if version >= SOL_VERSION_1_6 else 0
    gc = read_int(f)
    lc = read_int(f)
    nc = read_int(f)
    pc = read_int(f)
    bc = read_int(f)
    hc = read_int(f)
    zc = read_int(f)
    jc = read_int(f)
    xc = read_int(f)
    rc = read_int(f)
    uc = read_int(f)
    wc = read_int(f)
    ic = read_int(f)

    counts = dict(ac=ac, dc=dc, mc=mc, vc=vc, ec=ec, sc=sc, tc=tc, oc=oc,
                  gc=gc, lc=lc, nc=nc, pc=pc, bc=bc, hc=hc, zc=zc,
                  jc=jc, xc=xc, rc=rc, uc=uc, wc=wc, ic=ic,
                  version=version)

    # Skip sections before jumps (same as fix_sol_balls.py)
    f.read(ac)            # text
    f.read(dc * 8)        # dicts

    for i in range(mc):   # materials (variable size)
        f.read(4 * 4)     # d[4]
        f.read(4 * 4)     # a[4]
        f.read(4 * 4)     # s[4]
        f.read(4 * 4)     # e[4]
        f.read(4 * 1)     # h[1]
        fl = read_int(f)   # fl
        f.read(PATHMAX)    # filename
        if version >= SOL_VERSION_1_6:
            if fl & M_ALPHA_TEST:
                f.read(4)  # alpha_func
                f.read(4)  # alpha_ref

    f.read(vc * 12)       # verts
    f.read(ec * 8)        # edges
    f.read(sc * 16)       # sides
    f.read(tc * 8)        # texcoords

    if version >= SOL_VERSION_1_6:
        f.read(oc * 12)   # offs

    if version >= SOL_VERSION_1_6:
        f.read(gc * 16)   # geoms (new format)
    else:
        f.read(gc * 40)

    f.read(lc * 36)       # lumps
    f.read(nc * 20)       # nodes

    for i in range(pc):   # paths (variable size)
        f.read(4 * 3)     # p[3]
        f.read(4)          # t
        f.read(4)          # pi
        f.read(4)          # f
        f.read(4)          # s
        fl = 0
        if version >= SOL_VERSION_1_6:
            fl = read_int(f)
        if fl & P_ORIENTED:
            f.read(4 * 4)  # e[4] quaternion

    for i in range(bc):   # bodies (variable size)
        f.read(4)          # pi
        if version >= SOL_VERSION_1_6:
            f.read(4)      # pj
        f.read(4)          # ni
        f.read(4)          # l0
        f.read(4)          # lc
        f.read(4)          # g0
        f.read(4)          # gc

    f.read(hc * 20)       # items
    f.read(zc * 16)       # goals

    jump_offset = f.tell()
    return jump_offset, counts


def pack_jump(p, q, r):
    """Pack a jump entry as 28 bytes (7 little-endian floats)."""
    return struct.pack('<7f', p[0], p[1], p[2], q[0], q[1], q[2], r)


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    sol_path = os.path.join(base, 'android', 'app', 'src', 'main',
                            'assets', 'data', 'map-paxed', 's.sol')

    if not os.path.exists(sol_path):
        print(f"ERROR: {sol_path} not found")
        sys.exit(1)

    # --- Parse header and find jump offset ---
    with open(sol_path, 'rb') as f:
        jump_offset, c = skip_to_jump_section(f)

    jc, xc, rc, uc, wc, ic = c['jc'], c['xc'], c['rc'], c['uc'], c['wc'], c['ic']
    print(f"Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc} ic={ic}")
    print(f"Jump section offset: {jump_offset}")

    assert jc == 8, f"Expected jc=8, got {jc}"
    assert xc == 0, f"Expected xc=0, got {xc}"
    assert len(JUMPS) == jc

    jump_size = jc * 28   # 224 bytes
    ball_offset = jump_offset + jump_size  # expected ball start
    ball_size = uc * 16
    view_offset_expected = ball_offset + ball_size  # expected view start

    print(f"Expected ball offset:  {ball_offset}")
    print(f"Expected view offset:  {view_offset_expected}")

    # --- Read the full file ---
    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())

    file_size = len(data)
    print(f"File size: {file_size}")

    # --- Verify ball data at expected offset ---
    for i in range(uc):
        off = ball_offset + i * 16
        px, py, pz, r = struct.unpack_from('<4f', data, off)
        print(f"  Ball[{i}] at {off}: p=({px:.3f}, {py:.3f}, {pz:.3f}) r={r:.4f}")

    # --- Find actual view data ---
    # Scan forward from expected view offset looking for valid view data.
    # View p coordinates should be reasonable level coords (not ball-like).
    actual_view_offset = None
    scan_start = view_offset_expected
    scan_end = min(scan_start + 256, file_size - wc * 24)

    for probe in range(scan_start, scan_end, 4):
        # Read 2 candidate views (wc=2) and check if they look reasonable
        if probe + wc * 24 > file_size:
            break
        views_ok = True
        for vi in range(wc):
            vp = struct.unpack_from('<6f', data, probe + vi * 24)
            # View coordinates should be finite and in a reasonable range
            for val in vp:
                if abs(val) > 1000 or val != val:  # NaN check
                    views_ok = False
                    break
            if not views_ok:
                break
        if views_ok:
            # Extra check: the data right after views should look like iv[] indices
            iv_start = probe + wc * 24
            if iv_start + 8 <= file_size:
                i0, i1 = struct.unpack_from('<2i', data, iv_start)
                if 0 <= i0 < 10000 and 0 <= i1 < 10000:
                    actual_view_offset = probe
                    break

    if actual_view_offset is None:
        print("ERROR: Could not find view section")
        sys.exit(1)

    extra_bytes = actual_view_offset - view_offset_expected
    print(f"Actual view offset:    {actual_view_offset}")
    print(f"Extra bytes to remove: {extra_bytes}")

    for vi in range(wc):
        vp = struct.unpack_from('<6f', data, actual_view_offset + vi * 24)
        print(f"  View[{vi}] at {actual_view_offset + vi*24}: "
              f"p=({vp[0]:.2f},{vp[1]:.2f},{vp[2]:.2f}) "
              f"q=({vp[3]:.2f},{vp[4]:.2f},{vp[5]:.2f})")

    # --- Build new jump section (8 clean entries, no sentinels) ---
    new_jumps = b''
    for p, q, r in JUMPS:
        new_jumps += pack_jump(p, q, r)
    assert len(new_jumps) == jump_size

    # --- Verify existing entries 0-5 match ---
    # Read with sentinel detection (same as C runtime)
    with open(sol_path, 'rb') as f:
        f.seek(jump_offset)
        for ji in range(6):
            pos = f.tell()
            v0 = struct.unpack('<i', f.read(4))[0]
            v1 = struct.unpack('<i', f.read(4))[0]
            if v0 != -1 or v1 != -1:
                f.seek(pos)
            p = struct.unpack('<3f', f.read(12))
            q = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            ep, eq, er = JUMPS[ji]
            ok = (abs(p[0]-ep[0])<0.001 and abs(p[1]-ep[1])<0.001 and
                  abs(p[2]-ep[2])<0.001 and abs(q[0]-eq[0])<0.001 and
                  abs(q[1]-eq[1])<0.001 and abs(q[2]-eq[2])<0.001 and
                  abs(r-er)<0.001)
            status = "OK" if ok else "MISMATCH"
            print(f"  Jump[{ji}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) "
                  f"q=({q[0]:.3f},{q[1]:.3f},{q[2]:.3f}) r={r:.1f} [{status}]")

    # --- Apply patches ---

    # Backup
    backup = sol_path + '.bak'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"\nBackup: {backup}")

    # 1. Replace jump section
    data[jump_offset:jump_offset + jump_size] = new_jumps

    # 2. Remove extra bytes between ball end and actual view start
    if extra_bytes > 0:
        remove_start = view_offset_expected
        remove_end = actual_view_offset
        del data[remove_start:remove_end]
        print(f"Removed {extra_bytes} bytes at offset {remove_start}-{remove_end}")

    # --- Write patched file ---
    with open(sol_path, 'wb') as f:
        f.write(data)

    new_size = len(data)
    print(f"\nPatched file: {new_size} bytes (was {file_size}, delta {new_size - file_size})")

    # --- Verify ---
    with open(sol_path, 'rb') as f:
        jump_off2, c2 = skip_to_jump_section(f)
        assert jump_off2 == jump_offset, "Jump offset changed!"

        # Read all 8 jumps cleanly (no sentinels needed)
        for ji in range(jc):
            p = struct.unpack('<3f', f.read(12))
            q = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            ep, eq, er = JUMPS[ji]
            ok = (abs(p[0]-ep[0])<0.001 and abs(p[1]-ep[1])<0.001 and
                  abs(p[2]-ep[2])<0.001)
            print(f"  Verify Jump[{ji}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) "
                  f"r={r:.1f} [{'OK' if ok else 'FAIL'}]")

        # Read balls
        for bi in range(uc):
            bp = struct.unpack('<4f', f.read(16))
            print(f"  Verify Ball[{bi}]: ({bp[0]:.3f},{bp[1]:.3f},{bp[2]:.3f}) r={bp[3]:.4f}")

        # Read views
        for wi in range(wc):
            vp = struct.unpack('<6f', f.read(24))
            print(f"  Verify View[{wi}]: p=({vp[0]:.2f},{vp[1]:.2f},{vp[2]:.2f}) "
                  f"q=({vp[3]:.2f},{vp[4]:.2f},{vp[5]:.2f})")

    print("\nDone. Rebuild with: ./gradlew assemblePuttDebug")


if __name__ == '__main__':
    main()
