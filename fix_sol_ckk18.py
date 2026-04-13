#!/usr/bin/env python3
"""
Fix map-ckk hole 18: remove 25 jump sentinels, reconstruct jumps 24-31,
fix balls and views. 32 teleporters all targeting t3=(0,28,0).

Root cause: fix_sol_balls.py wrote 200 bytes too early (25 sentinel pairs),
destroying jumps 24-31, all ball data, and all view data (NaN = black screen).
"""

import struct
import os
import sys
import shutil

SOL_VERSION_1_6 = 7
M_ALPHA_TEST = 1 << 9
P_ORIENTED = 1
PATHMAX = 64


def read_int(f):
    return struct.unpack('<i', f.read(4))[0]


def skip_to_goal_end(f):
    magic = read_int(f)
    version = read_int(f)
    expected_magic = 0xAF | (ord('S') << 8) | (ord('O') << 16) | (ord('L') << 24)
    assert magic == expected_magic, f"Bad magic: 0x{magic:08X}"
    assert version == 9, f"Expected version 9, got {version}"

    ac = read_int(f); dc = read_int(f); mc = read_int(f)
    vc = read_int(f); ec = read_int(f); sc = read_int(f)
    tc = read_int(f)
    oc = read_int(f) if version >= SOL_VERSION_1_6 else 0
    gc = read_int(f); lc = read_int(f); nc = read_int(f)
    pc = read_int(f); bc = read_int(f); hc = read_int(f)
    zc = read_int(f); jc = read_int(f); xc = read_int(f)
    rc = read_int(f); uc = read_int(f); wc = read_int(f)
    ic = read_int(f)

    counts = dict(ac=ac, dc=dc, mc=mc, vc=vc, ec=ec, sc=sc, tc=tc, oc=oc,
                  gc=gc, lc=lc, nc=nc, pc=pc, bc=bc, hc=hc, zc=zc,
                  jc=jc, xc=xc, rc=rc, uc=uc, wc=wc, ic=ic, version=version)

    f.read(ac); f.read(dc * 8)
    for _ in range(mc):
        f.read(4*4 + 4*4 + 4*4 + 4*4 + 4)
        fl = read_int(f); f.read(PATHMAX)
        if version >= SOL_VERSION_1_6 and (fl & M_ALPHA_TEST): f.read(8)
    f.read(vc * 12); f.read(ec * 8); f.read(sc * 16); f.read(tc * 8)
    if version >= SOL_VERSION_1_6: f.read(oc * 12)
    f.read(gc * 16 if version >= SOL_VERSION_1_6 else gc * 40)
    f.read(lc * 36); f.read(nc * 20)
    for _ in range(pc):
        f.read(4*3 + 4 + 4 + 4 + 4)
        fl = 0
        if version >= SOL_VERSION_1_6: fl = read_int(f)
        if fl & P_ORIENTED: f.read(4*4)
    for _ in range(bc):
        f.read(4)
        if version >= SOL_VERSION_1_6: f.read(4)
        f.read(4*5)
    f.read(hc * 20)
    f.read(zc * 16)
    return f.tell(), counts


def pack_jump(p, q, r):
    return struct.pack('<7f', p[0], p[1], p[2], q[0], q[1], q[2], r)

def pack_ball(p, r):
    return struct.pack('<4f', p[0], p[1], p[2], r)

def pack_view(p, q):
    return struct.pack('<6f', p[0], p[1], p[2], q[0], q[1], q[2])


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    sol_path = os.path.join(base, 'android', 'app', 'src', 'main',
                            'assets', 'data', 'map-ckk', '18.sol')

    if not os.path.exists(sol_path):
        print(f"ERROR: {sol_path} not found"); sys.exit(1)

    print(f"{'='*60}")
    print(f"Fixing hole 18: {sol_path}")

    # All 32 teleporters target t3 = (0,28,0), r=0.5
    # SOL order matches entity order (12-43)
    T3 = (0.0, 28.0, 0.0)
    R = 0.5
    jumps = [
        # Group 1: y=5504, z=-80 (entities 12-16, 43)
        ((1.0, -1.25, -86.0), T3, R),      # [0]  e12
        ((-5.0, -1.25, -86.0), T3, R),     # [1]  e13
        ((-3.0, -1.25, -86.0), T3, R),     # [2]  e14
        ((-1.0, -1.25, -86.0), T3, R),     # [3]  e15
        ((3.0, -1.25, -86.0), T3, R),      # [4]  e16
        # Group 2: y=5504, z=-128 (entities 17-21)
        ((-5.0, -2.0, -86.0), T3, R),      # [5]  e17
        ((-3.0, -2.0, -86.0), T3, R),      # [6]  e18
        ((-1.0, -2.0, -86.0), T3, R),      # [7]  e19
        ((1.0, -2.0, -86.0), T3, R),       # [8]  e20
        ((3.0, -2.0, -86.0), T3, R),       # [9]  e21
        # Group 3: y=1184, z=1392 (entities 22-23, 25-26, 28)
        ((5.0, 21.75, -18.5), T3, R),      # [10] e22
        ((-5.0, 21.75, -18.5), T3, R),     # [11] e23
        ((-5.0, 22.5, -18.5), T3, R),      # [12] e24
        ((-1.0, 21.75, -18.5), T3, R),     # [13] e25
        ((-3.0, 21.75, -18.5), T3, R),     # [14] e26
        # Group 4: y=1184, z=1440 (entities 27, 29-31)
        ((-3.0, 22.5, -18.5), T3, R),      # [15] e27
        ((3.0, 21.75, -18.5), T3, R),      # [16] e28
        ((-1.0, 22.5, -18.5), T3, R),      # [17] e29
        ((5.0, 22.5, -18.5), T3, R),       # [18] e30
        ((3.0, 22.5, -18.5), T3, R),       # [19] e31
        # Group 5: y=2720, z=864 (entities 32-33, 35-36, 38)
        ((5.0, 13.5, -42.5), T3, R),       # [20] e32
        ((-5.0, 13.5, -42.5), T3, R),      # [21] e33
        ((-5.0, 14.25, -42.5), T3, R),     # [22] e34
        ((-1.0, 13.5, -42.5), T3, R),      # [23] e35
        ((1.0, 13.5, -42.5), T3, R),       # [24] e36
        # Group 6: y=2720, z=912 (entities 37, 39-41)
        ((1.0, 14.25, -42.5), T3, R),      # [25] e37
        ((3.0, 13.5, -42.5), T3, R),       # [26] e38
        ((-1.0, 14.25, -42.5), T3, R),     # [27] e39
        ((5.0, 14.25, -42.5), T3, R),      # [28] e40
        ((3.0, 14.25, -42.5), T3, R),      # [29] e41
        # Remaining (entities 42-43, same area as groups 1-2)
        ((5.0, -2.0, -86.0), T3, R),       # [30] e42
        ((5.0, -1.25, -86.0), T3, R),      # [31] e43
    ]
    assert len(jumps) == 32

    # Ball: origin=(0,0,1816) r=0.0625 -> (0, (1816-24)/64+0.0625+0.0005, 0)
    ball = ((0.0, 28.063, 0.0), 0.0625)

    # View[0] (e7): origin=(-1452,-550,2592) target=t1->e8:(2333,2722,311)
    # View[1] (e9): origin=(-1452,2726,2592) target=t2->e10:(2333,-546,311)
    views = [
        ((-1452/64, 2592/64, 550/64), (2333/64, 311/64, -2722/64)),
        ((-1452/64, 2592/64, -2726/64), (2333/64, 311/64, 546/64)),
    ]

    # === Parse ===
    with open(sol_path, 'rb') as f:
        goal_end, c = skip_to_goal_end(f)

    jc, xc, rc, uc, wc, ic = c['jc'], c['xc'], c['rc'], c['uc'], c['wc'], c['ic']
    print(f"  Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc} ic={ic}")
    assert jc == 32 and xc == 0 and rc == 0 and uc == 5 and wc == 2

    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())
    file_size = len(data)
    iv_start = file_size - ic * 4

    old_region_size = iv_start - goal_end
    new_region_size = jc * 28 + uc * 16 + wc * 24
    print(f"  Goal end: {goal_end}, iv start: {iv_start}")
    print(f"  Region: {old_region_size} -> {new_region_size} bytes")

    # === Diagnostics: count sentinels and verify first 24 jumps ===
    pos = goal_end
    sentinels = 0
    corrupted = 0
    for ji in range(jc):
        v0, v1 = struct.unpack_from('<2i', data, pos)
        if v0 == -1 and v1 == -1:
            sentinels += 1
            pos += 8
        jp = struct.unpack_from('<3f', data, pos)
        jr = struct.unpack_from('<f', data, pos + 24)[0]
        exp = jumps[ji]
        p_ok = all(abs(jp[i] - exp[0][i]) < 0.02 for i in range(3))
        r_ok = abs(jr - exp[2]) < 0.02
        if not p_ok or not r_ok:
            corrupted += 1
            if ji < 5 or ji >= 24:  # only print first/last corrupted
                print(f"    Jump[{ji}]: p=({jp[0]:.3f},{jp[1]:.3f},{jp[2]:.3f}) "
                      f"r={jr:.3f} ** CORRUPT")
        pos += 28
    print(f"  Sentinels: {sentinels}, corrupted jumps: {corrupted}")

    # === Build clean region ===
    new_region = b''
    for p, q, r in jumps:
        new_region += pack_jump(p, q, r)
    for _ in range(uc):
        new_region += pack_ball(ball[0], ball[1])
    for p, q in views:
        new_region += pack_view(p, q)
    assert len(new_region) == new_region_size

    # === Backup and patch ===
    backup = sol_path + '.bak2'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"  Backup: {backup}")

    patched = data[:goal_end] + new_region + data[iv_start:]
    with open(sol_path, 'wb') as f:
        f.write(patched)
    print(f"  Patched: {len(patched)} bytes (was {file_size}, delta {len(patched)-file_size})")

    # === Verify ===
    print(f"\n  Verification:")
    with open(sol_path, 'rb') as f:
        _, c2 = skip_to_goal_end(f)

        ok_count = 0
        for ji in range(jc):
            p = struct.unpack('<3f', f.read(12))
            q = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            exp = jumps[ji]
            p_ok = all(abs(p[i] - exp[0][i]) < 0.001 for i in range(3))
            q_ok = all(abs(q[i] - exp[1][i]) < 0.001 for i in range(3))
            r_ok = abs(r - exp[2]) < 0.001
            if p_ok and q_ok and r_ok:
                ok_count += 1
            else:
                print(f"    Jump[{ji}]: MISMATCH p={p} q={q} r={r}")
        print(f"    Jumps: {ok_count}/32 OK")

        for bi in range(uc):
            bp = struct.unpack('<3f', f.read(12))
            br = struct.unpack('<f', f.read(4))[0]
            if bi == 0:
                print(f"    Ball[0]: p=({bp[0]:.4f},{bp[1]:.4f},{bp[2]:.4f}) r={br:.4f}")

        for wi in range(wc):
            vp = struct.unpack('<6f', f.read(24))
            print(f"    View[{wi}]: p=({vp[0]:.3f},{vp[1]:.3f},{vp[2]:.3f}) "
                  f"q=({vp[3]:.3f},{vp[4]:.3f},{vp[5]:.3f})")

        pos = f.tell()
        first_iv = struct.unpack('<4i', f.read(16))
        print(f"    iv[] at {pos}: first 4 = {first_iv}")
        assert first_iv[0] >= 0 and first_iv[0] < 10000, f"iv[0] looks wrong: {first_iv[0]}"

    print(f"    OK")
    print(f"\n{'='*60}")
    print("Done. Rebuild with: ./gradlew assemblePuttDebug")


if __name__ == '__main__':
    main()
