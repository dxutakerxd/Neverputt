#!/usr/bin/env python3
"""
Fix map-ckk holes 14, 16, and 17: remove sentinel pairs and ball-extra bytes,
rewrite jump/goal/ball/view sections with correct data from MAP.

Hole 14: 4 jump sentinels, Jump[3] r=0 and Jump[4] corrupted by fix_sol_balls.py
Hole 16: 1 goal sentinel + 2 jump sentinels, Jump[1] corrupted
Hole 17: 9 jump sentinels, Jump[6] destination bug (infinite teleporter loop),
         56 billboards preserved, corrupted ball/view positions
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


def skip_to_section(f, stop_at='jumps'):
    """Parse SOL header and skip to the specified section boundary.
    stop_at='goals': stop before goal section (after items)
    stop_at='jumps': stop before jump section (after goals)
    Returns (offset, counts_dict).
    """
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

    f.read(ac)
    f.read(dc * 8)
    for _ in range(mc):
        f.read(4*4 + 4*4 + 4*4 + 4*4 + 4)
        fl = read_int(f)
        f.read(PATHMAX)
        if version >= SOL_VERSION_1_6 and (fl & M_ALPHA_TEST):
            f.read(8)
    f.read(vc * 12)
    f.read(ec * 8)
    f.read(sc * 16)
    f.read(tc * 8)
    if version >= SOL_VERSION_1_6:
        f.read(oc * 12)
    f.read(gc * 16 if version >= SOL_VERSION_1_6 else gc * 40)
    f.read(lc * 36)
    f.read(nc * 20)
    for _ in range(pc):
        f.read(4*3 + 4 + 4 + 4 + 4)
        fl = 0
        if version >= SOL_VERSION_1_6:
            fl = read_int(f)
        if fl & P_ORIENTED:
            f.read(4*4)
    for _ in range(bc):
        f.read(4)
        if version >= SOL_VERSION_1_6:
            f.read(4)
        f.read(4*5)
    f.read(hc * 20)

    if stop_at == 'goals':
        return f.tell(), counts

    f.read(zc * 16)
    return f.tell(), counts


def pack_goal(p, r):
    return struct.pack('<4f', p[0], p[1], p[2], r)


def pack_jump(p, q, r):
    return struct.pack('<7f', p[0], p[1], p[2], q[0], q[1], q[2], r)


def pack_ball(p, r):
    return struct.pack('<4f', p[0], p[1], p[2], r)


def pack_view(p, q):
    return struct.pack('<6f', p[0], p[1], p[2], q[0], q[1], q[2])


def fix_hole_14(sol_path):
    """Fix 14.sol: remove 4 jump sentinels, rewrite all jumps/balls/views."""
    print(f"\n{'='*60}")
    print(f"Fixing hole 14: {sol_path}")

    # Correct values from 14.map
    # Jumps sorted by entity number (SOL order)
    jumps = [
        # Jump[0] (e5): origin=(392,592,-8) target=t3->e6:(0,-136,8) r=0.125
        ((6.125, -0.125, -9.25), (0.0, 0.125, 2.125), 0.125),
        # Jump[1] (e7): origin=(-136,96,8) target=t4->e16:(0,886,-32) r=0.125
        ((-2.125, 0.125, -1.5), (0.0, -0.5, -13.84375), 0.125),
        # Jump[2] (e8): origin=(136,96,8) target=t4->e16:(0,886,-32) r=0.125
        ((2.125, 0.125, -1.5), (0.0, -0.5, -13.84375), 0.125),
        # Jump[3] (e15): origin=(0,424,-32) target=t3->e6:(0,-136,8) r=0.125
        ((0.0, -0.5, -6.625), (0.0, 0.125, 2.125), 0.125),
        # Jump[4] (e17): origin=(-392,592,-8) target=t3->e6:(0,-136,8) r=0.125
        ((-6.125, -0.125, -9.25), (0.0, 0.125, 2.125), 0.125),
    ]

    # Ball: origin=(0,0,24) r=0.0625 -> p=(0, (24-24)/64+0.0625+0.0005, 0)
    ball = ((0.0, 0.063, 0.0), 0.0625)

    views = [
        # View[0] (e10): origin=(-475,-114,249) target=t1->e11:(101,132,-211)
        ((-475/64, 249/64, 114/64), (101/64, -211/64, -132/64)),
        # View[1] (e13): origin=(-16,-16,88) target=t2->e14:(58,85,505)
        ((-16/64, 88/64, 16/64), (58/64, 505/64, -85/64)),
    ]

    with open(sol_path, 'rb') as f:
        goal_end, c = skip_to_section(f, 'jumps')

    jc, xc, rc, uc, wc, ic = c['jc'], c['xc'], c['rc'], c['uc'], c['wc'], c['ic']
    print(f"  Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc} ic={ic}")
    assert jc == 5 and xc == 0 and rc == 0 and uc == 5 and wc == 2

    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())
    file_size = len(data)
    iv_start = file_size - ic * 4

    old_region_size = iv_start - goal_end
    new_region_size = jc * 28 + uc * 16 + wc * 24
    print(f"  Goal end: {goal_end}, iv start: {iv_start}")
    print(f"  Region: {old_region_size} -> {new_region_size} bytes")

    # Diagnostics
    pos = goal_end
    sentinels = 0
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
        print(f"    Jump[{ji}]: p=({jp[0]:.3f},{jp[1]:.3f},{jp[2]:.3f}) "
              f"r={jr:.4f} {'OK' if p_ok and r_ok else '** FIX'}")
        pos += 28
    print(f"  Sentinels: {sentinels}")

    # Build clean region
    new_region = b''
    for p, q, r in jumps:
        new_region += pack_jump(p, q, r)
    for _ in range(uc):
        new_region += pack_ball(ball[0], ball[1])
    for p, q in views:
        new_region += pack_view(p, q)
    assert len(new_region) == new_region_size

    # Backup and patch
    backup = sol_path + '.bak2'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"  Backup: {backup}")

    patched = data[:goal_end] + new_region + data[iv_start:]
    with open(sol_path, 'wb') as f:
        f.write(patched)
    print(f"  Patched: {len(patched)} bytes (was {file_size}, delta {len(patched)-file_size})")

    verify_hole(sol_path, 'jumps', jc=5, xc=0, rc=0, uc=5, wc=2)


def fix_hole_16(sol_path):
    """Fix 16.sol: remove goal+jump sentinels, rewrite goals/jumps/balls/views."""
    print(f"\n{'='*60}")
    print(f"Fixing hole 16: {sol_path}")

    # Goals use formula: p = (x/64, (z-24)/64, -y/64)
    goals = [
        # Goal[0] (e6): origin=(-1152, 128, 420) r=0.1375
        ((-18.0, 6.1875, -2.0), 0.1375),
        # Goal[1] (e11): origin=(960, 3328, 8) r=0.1375
        ((15.0, -0.25, -52.0), 0.1375),
    ]

    jumps = [
        # Jump[0] (e12): origin=(-336,-32,496) target=t3->e15:(0,-256,0) r=0.5
        ((-5.25, 7.75, 0.5), (0.0, 0.0, 4.0), 0.5),
        # Jump[1] (e13): origin=(0,-256,0) target=t4->e14:(-336,-32,496) r=0.5
        ((0.0, 0.0, 4.0), (-5.25, 7.75, 0.5), 0.5),
    ]

    ball = ((0.0, 0.063, 0.0), 0.0625)

    views = [
        # View[0] (e7): origin=(-831,-521,1745) target=t1->e8:(995,1319,-544)
        ((-831/64, 1745/64, 521/64), (995/64, -544/64, -1319/64)),
        # View[1] (e9): origin=(435,199,933) target=t2->e10:(435,195,1695)
        ((435/64, 933/64, -199/64), (435/64, 1695/64, -195/64)),
    ]

    # Parse to start of goals (before goal section)
    with open(sol_path, 'rb') as f:
        goals_start, c = skip_to_section(f, 'goals')

    zc, jc, xc, rc, uc, wc, ic = (c['zc'], c['jc'], c['xc'], c['rc'],
                                    c['uc'], c['wc'], c['ic'])
    print(f"  Header: zc={zc} jc={jc} xc={xc} rc={rc} uc={uc} wc={wc} ic={ic}")
    assert zc == 2 and jc == 2 and xc == 0 and rc == 0 and uc == 5 and wc == 2

    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())
    file_size = len(data)
    iv_start = file_size - ic * 4

    old_region_size = iv_start - goals_start
    new_region_size = zc * 16 + jc * 28 + uc * 16 + wc * 24
    print(f"  Goals start: {goals_start}, iv start: {iv_start}")
    print(f"  Region: {old_region_size} -> {new_region_size} bytes")

    # Diagnostics
    pos = goals_start
    sentinels = 0
    for zi in range(zc):
        v0, v1 = struct.unpack_from('<2i', data, pos)
        if v0 == -1 and v1 == -1:
            sentinels += 1
            print(f"    Goal[{zi}] SENTINEL at {pos}")
            pos += 8
        gp = struct.unpack_from('<3f', data, pos)
        gr = struct.unpack_from('<f', data, pos + 12)[0]
        exp = goals[zi]
        ok = all(abs(gp[i] - exp[0][i]) < 0.02 for i in range(3)) and abs(gr - exp[1]) < 0.02
        print(f"    Goal[{zi}]: p=({gp[0]:.4f},{gp[1]:.4f},{gp[2]:.4f}) "
              f"r={gr:.4f} {'OK' if ok else '** FIX'}")
        pos += 16

    for ji in range(jc):
        v0, v1 = struct.unpack_from('<2i', data, pos)
        if v0 == -1 and v1 == -1:
            sentinels += 1
            print(f"    Jump[{ji}] SENTINEL at {pos}")
            pos += 8
        jp = struct.unpack_from('<3f', data, pos)
        jq = struct.unpack_from('<3f', data, pos + 12)
        jr = struct.unpack_from('<f', data, pos + 24)[0]
        exp = jumps[ji]
        p_ok = all(abs(jp[i] - exp[0][i]) < 0.02 for i in range(3))
        print(f"    Jump[{ji}]: p=({jp[0]:.3f},{jp[1]:.3f},{jp[2]:.3f}) "
              f"q=({jq[0]:.3f},{jq[1]:.3f},{jq[2]:.3f}) r={jr:.3f} "
              f"{'OK' if p_ok else '** FIX'}")
        pos += 28
    print(f"  Sentinels: {sentinels}")

    # Build clean region
    new_region = b''
    for p, r in goals:
        new_region += pack_goal(p, r)
    for p, q, r in jumps:
        new_region += pack_jump(p, q, r)
    for _ in range(uc):
        new_region += pack_ball(ball[0], ball[1])
    for p, q in views:
        new_region += pack_view(p, q)
    assert len(new_region) == new_region_size

    # Backup and patch
    backup = sol_path + '.bak2'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"  Backup: {backup}")

    patched = data[:goals_start] + new_region + data[iv_start:]
    with open(sol_path, 'wb') as f:
        f.write(patched)
    print(f"  Patched: {len(patched)} bytes (was {file_size}, delta {len(patched)-file_size})")

    verify_hole(sol_path, 'goals', zc=2, jc=2, xc=0, rc=0, uc=5, wc=2)


def fix_hole_17(sol_path):
    """Fix 17.sol: remove 9 jump sentinels, fix Jump[6] teleporter destination,
    preserve 56 billboards, fix balls and views."""
    print(f"\n{'='*60}")
    print(f"Fixing hole 17: {sol_path}")

    jumps = [
        # Jump[0] (e6): origin=(0,2432,-48) target=t3->e12:(0,2752,-48) r=0.5
        ((0.0, -0.75, -38.0), (0.0, -0.75, -43.0), 0.5),
        # Jump[1] (e7): origin=(0,4416,-48) target=t7->e11:(0,4800,-48) r=0.5
        ((0.0, -0.75, -69.0), (0.0, -0.75, -75.0), 0.5),
        # Jump[2] (e8): origin=(0,2880,-48) target=t4->e13:(0,3264,-48) r=0.5
        ((0.0, -0.75, -45.0), (0.0, -0.75, -51.0), 0.5),
        # Jump[3] (e9): origin=(0,3392,-48) target=t5->e14:(0,3776,-48) r=0.5
        ((0.0, -0.75, -53.0), (0.0, -0.75, -59.0), 0.5),
        # Jump[4] (e10): origin=(0,3904,-48) target=t6->e15:(0,4288,-48) r=0.5
        ((0.0, -0.75, -61.0), (0.0, -0.75, -67.0), 0.5),
        # Jump[5] (e78): origin=(0,6912,-64) target=t8->e79:(0,6912,72) r=0.125
        ((0.0, -1.0, -108.0), (0.0, 1.125, -108.0), 0.125),
        # Jump[6] (e80): origin=(0,5376,-368) target=t9->e81:(0,5248,272)
        # DESIGN FIX: q[2] changed from -82.0 to -86.0 to break infinite loop
        ((0.0, -5.75, -84.0), (0.0, 4.25, -86.0), 0.5),
        # Jump[7] (e82): origin=(0,5376,272) target=t10->e83:(0,5376,-368) r=0.5
        ((0.0, 4.25, -84.0), (0.0, -5.75, -84.0), 0.5),
        # Jump[8] (e84): origin=(0,6528,272) target=t11->e85:(0,512,608) r=0.5
        ((0.0, 4.25, -102.0), (0.0, 9.5, -8.0), 0.5),
    ]

    # Ball: origin=(0,0,280) r=0.0625 -> p=(0, (280-24)/64+0.0625+0.0005, 0)
    ball = ((0.0, 4.063, 0.0), 0.0625)

    views = [
        # View[0] (e87): origin=(-984,-84,1747) target=t2->e90:(353,1555,-466)
        ((-984/64, 1747/64, 84/64), (353/64, -466/64, -1555/64)),
        # View[1] (e89): origin=(-985,-85,1746) target=t2->e90:(353,1555,-466)
        ((-985/64, 1746/64, 85/64), (353/64, -466/64, -1555/64)),
    ]

    with open(sol_path, 'rb') as f:
        goal_end, c = skip_to_section(f, 'jumps')

    jc, xc, rc, uc, wc, ic = c['jc'], c['xc'], c['rc'], c['uc'], c['wc'], c['ic']
    print(f"  Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc} ic={ic}")
    assert jc == 9 and xc == 0 and rc == 56 and uc == 5 and wc == 2

    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())
    file_size = len(data)
    iv_start = file_size - ic * 4

    old_region_size = iv_start - goal_end
    new_region_size = jc * 28 + rc * 88 + uc * 16 + wc * 24
    print(f"  Goal end: {goal_end}, iv start: {iv_start}")
    print(f"  Region: {old_region_size} -> {new_region_size} bytes")

    # Walk through jumps with sentinel detection to find billboard start
    pos = goal_end
    sentinels = 0
    for ji in range(jc):
        v0, v1 = struct.unpack_from('<2i', data, pos)
        if v0 == -1 and v1 == -1:
            sentinels += 1
            pos += 8
        jp = struct.unpack_from('<3f', data, pos)
        jq = struct.unpack_from('<3f', data, pos + 12)
        jr = struct.unpack_from('<f', data, pos + 24)[0]
        exp = jumps[ji]
        p_ok = all(abs(jp[i] - exp[0][i]) < 0.02 for i in range(3))
        print(f"    Jump[{ji}]: p=({jp[0]:.3f},{jp[1]:.3f},{jp[2]:.3f}) "
              f"q=({jq[0]:.3f},{jq[1]:.3f},{jq[2]:.3f}) r={jr:.3f} "
              f"{'OK' if p_ok else '** FIX'}")
        pos += 28
    print(f"  Sentinels: {sentinels}")

    # Extract billboard data (starts right after sentinel-aware jump reading)
    billboard_start = pos
    billboard_size = rc * 88
    billboard_data = bytes(data[billboard_start:billboard_start + billboard_size])
    print(f"  Billboards: {rc} entries, {billboard_size} bytes at offset {billboard_start}")

    # Check for billboard corruption from fix_sol_balls.py
    fsb_offset = goal_end + jc * 28 + xc * 40 + rc * 88  # where fix_sol_balls.py wrote
    corrupt_into_billboard = fsb_offset - billboard_start
    if 0 < corrupt_into_billboard < billboard_size:
        corrupt_bytes = billboard_size - corrupt_into_billboard
        print(f"  ** Last {corrupt_bytes} bytes of billboard section corrupted (cosmetic)")

    # Build clean region
    new_region = b''
    for p, q, r in jumps:
        new_region += pack_jump(p, q, r)
    new_region += billboard_data
    for _ in range(uc):
        new_region += pack_ball(ball[0], ball[1])
    for p, q in views:
        new_region += pack_view(p, q)
    assert len(new_region) == new_region_size

    # Backup and patch
    backup = sol_path + '.bak2'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"  Backup: {backup}")

    patched = data[:goal_end] + new_region + data[iv_start:]
    with open(sol_path, 'wb') as f:
        f.write(patched)
    print(f"  Patched: {len(patched)} bytes (was {file_size}, delta {len(patched)-file_size})")

    verify_hole(sol_path, 'jumps', jc=9, xc=0, rc=56, uc=5, wc=2)


def verify_hole(sol_path, start_section, jc=0, xc=0, rc=0, uc=0, wc=0, zc=0):
    """Verify patched file by reading back all sections cleanly."""
    print(f"\n  Verification:")

    with open(sol_path, 'rb') as f:
        if start_section == 'goals':
            _, c = skip_to_section(f, 'goals')
            for zi in range(zc):
                gp = struct.unpack('<3f', f.read(12))
                gr = struct.unpack('<f', f.read(4))[0]
                print(f"    Goal[{zi}]: p=({gp[0]:.4f},{gp[1]:.4f},{gp[2]:.4f}) r={gr:.4f}")
        else:
            _, c = skip_to_section(f, 'jumps')

        for ji in range(jc):
            p = struct.unpack('<3f', f.read(12))
            q = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            print(f"    Jump[{ji}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) "
                  f"q=({q[0]:.3f},{q[1]:.3f},{q[2]:.3f}) r={r:.4f}")

        for xi in range(xc):
            p = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            pi = struct.unpack('<i', f.read(4))[0]
            f.read(20)  # t, t0, f, e, i
            print(f"    Swch[{xi}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) r={r:.3f} pi={pi}")

        f.read(rc * 88)  # skip billboards

        for bi in range(uc):
            bp = struct.unpack('<3f', f.read(12))
            br = struct.unpack('<f', f.read(4))[0]
            print(f"    Ball[{bi}]: p=({bp[0]:.4f},{bp[1]:.4f},{bp[2]:.4f}) r={br:.4f}")

        for wi in range(wc):
            vp = struct.unpack('<6f', f.read(24))
            print(f"    View[{wi}]: p=({vp[0]:.3f},{vp[1]:.3f},{vp[2]:.3f}) "
                  f"q=({vp[3]:.3f},{vp[4]:.3f},{vp[5]:.3f})")

        pos = f.tell()
        first_iv = struct.unpack('<4i', f.read(16))
        print(f"    iv[] at {pos}: first 4 = {first_iv}")
        assert first_iv[0] >= 0 and first_iv[0] < 10000, f"iv[0] looks wrong: {first_iv[0]}"

    print(f"    OK")


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(base, 'android', 'app', 'src', 'main',
                          'assets', 'data', 'map-ckk')

    sol_14 = os.path.join(assets, '14.sol')
    sol_16 = os.path.join(assets, '16.sol')
    sol_17 = os.path.join(assets, '17.sol')

    for sol in [sol_14, sol_16, sol_17]:
        if not os.path.exists(sol):
            print(f"ERROR: {sol} not found")
            sys.exit(1)

    fix_hole_14(sol_14)
    fix_hole_16(sol_16)
    fix_hole_17(sol_17)

    print(f"\n{'='*60}")
    print("Done. Rebuild with: ./gradlew assemblePuttDebug")


if __name__ == '__main__':
    main()
