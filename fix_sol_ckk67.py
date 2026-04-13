#!/usr/bin/env python3
"""
Fix map-ckk holes 6 and 7: remove sentinel pairs and ball-extra bytes,
rewrite jump/switch + ball + view sections with correct data from MAP.

Problem:
  Both SOL files have an 8-byte sentinel pair (0xFFFFFFFF x2) before
  the jump (hole 6) or switch (hole 7) section. The C runtime skips
  these sentinels, reading ball data 8 bytes later than fix_sol_balls.py
  expects. This causes:
    - Ball coordinates rotated (p[2],r,p[0],p[1] instead of p[0],p[1],p[2],r)
    - View data misaligned (reads ball remnants as view position)
    - Jump/switch tail data corrupted by ball-extra floats

Fix:
  Rewrite the region from goal-end to iv[]-start without sentinels
  and without extra ball bytes. All values computed from .map sources.
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
    """Parse SOL header and skip to the end of the goal section.
    Returns (goal_end_offset, counts_dict)."""

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

    # Skip sections before goals
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
    f.read(zc * 16)  # goals

    return f.tell(), counts


def find_iv_start(data, search_from, file_size):
    """Find iv[] start by looking for sequential small integers (0, 1, 2, 3)."""
    for probe in range(search_from, min(search_from + 512, file_size - 16), 4):
        vals = struct.unpack_from('<4i', data, probe)
        if vals == (0, 1, 2, 3):
            return probe
    return None


def pack_jump(p, q, r):
    """Pack a 28-byte jump entry."""
    return struct.pack('<7f', p[0], p[1], p[2], q[0], q[1], q[2], r)


def pack_switch(p, r, pi, t, t0, f, e, i):
    """Pack a 40-byte switch entry."""
    return struct.pack('<3f f i f f i i i',
                       p[0], p[1], p[2], r, pi, t, t0, f, e, i)


def pack_ball(p, r):
    """Pack a 16-byte ball entry."""
    return struct.pack('<4f', p[0], p[1], p[2], r)


def pack_view(p, q):
    """Pack a 24-byte view entry."""
    return struct.pack('<6f', p[0], p[1], p[2], q[0], q[1], q[2])


def fix_hole_06(sol_path):
    """Fix map-ckk/06.sol: remove jump sentinel + ball extras, write correct data."""

    print(f"\n{'='*60}")
    print(f"Fixing: {sol_path}")

    # --- Correct values from 06.map ---

    # Jump[0] (entity 6): origin=(0, 1536, -520), target=t3 (entity 8: origin 0, 1808, -496), r=1.0
    jump = (
        (0.0, -8.125, -24.0),      # p = (x/64, z/64, -y/64)
        (0.0, -7.75, -28.25),       # q from target t3
        1.0                          # r from MAP
    )

    # Ball (entity 1): origin=(0, 160, 24), radius=0.0625
    # p = (0/64, (24-24)/64 + 0.0625 + 0.0005, -160/64)
    ball = ((0.0, 0.063, -2.5), 0.0625)

    # View[0] (entity 13): origin=(-772.375, -684.875, 525.125), target=t1 (entity 15: 555.75, 998.375, -467.375)
    view0 = (
        (-772.375/64, 525.125/64, 684.875/64),
        (555.75/64, -467.375/64, -998.375/64)
    )

    # View[1] (entity 16): origin=(-1419, 506, 1102), target=t2 (entity 14: 656, 1376, 64)
    view1 = (
        (-1419.0/64, 1102.0/64, -506.0/64),
        (656.0/64, 64.0/64, -1376.0/64)
    )

    # --- Parse and find boundaries ---
    with open(sol_path, 'rb') as f:
        goal_end, c = skip_to_goal_end(f)

    jc, xc, rc, uc, wc = c['jc'], c['xc'], c['rc'], c['uc'], c['wc']
    print(f"  Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc}")
    assert jc == 1, f"Expected jc=1, got {jc}"
    assert xc == 0, f"Expected xc=0, got {xc}"
    assert rc == 0, f"Expected rc=0, got {rc}"
    assert uc == 5, f"Expected uc=5, got {uc}"
    assert wc == 2, f"Expected wc=2, got {wc}"

    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())

    iv_start = find_iv_start(data, goal_end, len(data))
    assert iv_start is not None, "Could not find iv[] start"

    old_region_size = iv_start - goal_end
    print(f"  Goal end: {goal_end}")
    print(f"  iv[] start: {iv_start}")
    print(f"  Old region size: {old_region_size} bytes")

    # --- Dump current state for diagnostics ---
    print(f"\n  Current state (sentinel-aware reading):")

    # Check for jump sentinel
    v0, v1 = struct.unpack_from('<2i', data, goal_end)
    has_sentinel = (v0 == -1 and v1 == -1)
    print(f"    Jump sentinel: {'YES' if has_sentinel else 'NO'} at {goal_end}")

    jump_data_start = goal_end + (8 if has_sentinel else 0)
    jp = struct.unpack_from('<3f', data, jump_data_start)
    jq = struct.unpack_from('<3f', data, jump_data_start + 12)
    jr = struct.unpack_from('<f', data, jump_data_start + 24)[0]
    print(f"    Jump[0]: p=({jp[0]:.3f},{jp[1]:.3f},{jp[2]:.3f}) "
          f"q=({jq[0]:.3f},{jq[1]:.3f},{jq[2]:.3f}) r={jr:.3f}")
    print(f"    Jump[0] EXPECTED: p=(0.000,-8.125,-24.000) q=(0.000,-7.750,-28.250) r=1.000")
    if abs(jq[2] - (-28.25)) > 0.01 or abs(jr - 1.0) > 0.01:
        print(f"    ** Jump q[2] and r are CORRUPTED (ball-extra data)")

    # --- Build clean region ---
    new_region = b''
    new_region += pack_jump(jump[0], jump[1], jump[2])
    for i in range(uc):
        new_region += pack_ball(ball[0], ball[1])
    new_region += pack_view(view0[0], view0[1])
    new_region += pack_view(view1[0], view1[1])

    new_region_size = len(new_region)
    expected_size = 28 + uc * 16 + wc * 24  # jump + balls + views
    assert new_region_size == expected_size, f"Region size mismatch: {new_region_size} vs {expected_size}"
    print(f"\n  New region size: {new_region_size} bytes (was {old_region_size}, saving {old_region_size - new_region_size})")

    # --- Backup and patch ---
    backup = sol_path + '.bak'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"  Backup: {backup}")

    # Replace old region with new
    patched = data[:goal_end] + new_region + data[iv_start:]

    with open(sol_path, 'wb') as f:
        f.write(patched)

    print(f"  Patched: {len(patched)} bytes (was {len(data)})")

    # --- Verify ---
    verify_hole(sol_path, jc=1, xc=0, uc=5, wc=2)


def fix_hole_07(sol_path):
    """Fix map-ckk/07.sol: remove switch sentinel + ball extras, write correct data."""

    print(f"\n{'='*60}")
    print(f"Fixing: {sol_path}")

    # --- Correct values from 07.map ---

    # Switch[0] (entity 11): info_camp at origin=(0, 256, -16), target=p1_0, timer=3
    # p = (0/64, -16/64, -256/64) = (0.0, -0.25, -4.0)
    # pi: p1_0 = entity 13 (path_corner, targetname=p1_0) = path index 0
    switch = {
        'p': (0.0, -0.25, -4.0),
        'r': 0.5,
        'pi': 0,
        't': 3.0,
        't0': 3.0,
        'f': 0,
        'e': 0,
        'i': 0,
    }

    # Ball (entity 1): origin=(-256, -512, -88), radius=0.0625
    # p = (-256/64, (-88-24)/64 + 0.0625 + 0.0005, 512/64) = (-4.0, -1.687, 8.0)
    ball = ((-4.0, -1.687, 8.0), 0.0625)

    # View[0] (entity 7): origin=(568, -965, 753), target=t1 (entity 9: -230, -72, -136)
    view0 = (
        (568.0/64, 753.0/64, 965.0/64),
        (-230.0/64, -136.0/64, 72.0/64)
    )

    # View[1] (entity 10): origin=(1776, 1616, 1184), target=t2 (entity 8: 473, 219, 9)
    view1 = (
        (1776.0/64, 1184.0/64, -1616.0/64),
        (473.0/64, 9.0/64, -219.0/64)
    )

    # --- Parse and find boundaries ---
    with open(sol_path, 'rb') as f:
        goal_end, c = skip_to_goal_end(f)

    jc, xc, rc, uc, wc = c['jc'], c['xc'], c['rc'], c['uc'], c['wc']
    print(f"  Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc}")
    assert jc == 0, f"Expected jc=0, got {jc}"
    assert xc == 1, f"Expected xc=1, got {xc}"
    assert rc == 0, f"Expected rc=0, got {rc}"
    assert uc == 5, f"Expected uc=5, got {uc}"
    assert wc == 2, f"Expected wc=2, got {wc}"

    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())

    iv_start = find_iv_start(data, goal_end, len(data))
    assert iv_start is not None, "Could not find iv[] start"

    old_region_size = iv_start - goal_end
    print(f"  Goal end: {goal_end}")
    print(f"  iv[] start: {iv_start}")
    print(f"  Old region size: {old_region_size} bytes")

    # --- Dump current state ---
    print(f"\n  Current state (sentinel-aware reading):")

    v0, v1 = struct.unpack_from('<2i', data, goal_end)
    has_sentinel = (v0 == -1 and v1 == -1)
    print(f"    Switch sentinel: {'YES' if has_sentinel else 'NO'} at {goal_end}")

    sw_data_start = goal_end + (8 if has_sentinel else 0)
    sp = struct.unpack_from('<3f', data, sw_data_start)
    sr = struct.unpack_from('<f', data, sw_data_start + 12)[0]
    spi = struct.unpack_from('<i', data, sw_data_start + 16)[0]
    st = struct.unpack_from('<f', data, sw_data_start + 20)[0]
    print(f"    Swch[0]: p=({sp[0]:.3f},{sp[1]:.3f},{sp[2]:.3f}) r={sr:.3f} pi={spi} t={st:.2f}")

    # --- Build clean region ---
    new_region = b''
    s = switch
    new_region += pack_switch(s['p'], s['r'], s['pi'], s['t'], s['t0'], s['f'], s['e'], s['i'])
    for i in range(uc):
        new_region += pack_ball(ball[0], ball[1])
    new_region += pack_view(view0[0], view0[1])
    new_region += pack_view(view1[0], view1[1])

    new_region_size = len(new_region)
    expected_size = xc * 40 + uc * 16 + wc * 24  # switch + balls + views
    assert new_region_size == expected_size, f"Region size mismatch: {new_region_size} vs {expected_size}"
    print(f"\n  New region size: {new_region_size} bytes (was {old_region_size}, saving {old_region_size - new_region_size})")

    # --- Backup and patch ---
    backup = sol_path + '.bak'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"  Backup: {backup}")

    # Replace old region with new
    patched = data[:goal_end] + new_region + data[iv_start:]

    with open(sol_path, 'wb') as f:
        f.write(patched)

    print(f"  Patched: {len(patched)} bytes (was {len(data)})")

    # --- Verify ---
    verify_hole(sol_path, jc=0, xc=1, uc=5, wc=2)


def verify_hole(sol_path, jc, xc, uc, wc):
    """Verify patched file by reading back all sections."""
    print(f"\n  Verification:")

    with open(sol_path, 'rb') as f:
        goal_end, c = skip_to_goal_end(f)

        # Read jumps (should be clean, no sentinels)
        for ji in range(jc):
            p = struct.unpack('<3f', f.read(12))
            q = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            print(f"    Jump[{ji}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) "
                  f"q=({q[0]:.3f},{q[1]:.3f},{q[2]:.3f}) r={r:.3f}")

        # Read switches (should be clean, no sentinels)
        for xi in range(xc):
            p = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            pi = struct.unpack('<i', f.read(4))[0]
            t = struct.unpack('<f', f.read(4))[0]
            t0 = struct.unpack('<f', f.read(4))[0]
            fv = struct.unpack('<i', f.read(4))[0]
            ev = struct.unpack('<i', f.read(4))[0]
            iv = struct.unpack('<i', f.read(4))[0]
            print(f"    Swch[{xi}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) "
                  f"r={r:.3f} pi={pi} t={t:.2f} f={fv} e={ev} i={iv}")

        # Read balls
        for bi in range(uc):
            bp = struct.unpack('<3f', f.read(12))
            br = struct.unpack('<f', f.read(4))[0]
            print(f"    Ball[{bi}]: p=({bp[0]:.4f},{bp[1]:.4f},{bp[2]:.4f}) r={br:.4f}")

        # Read views
        for wi in range(wc):
            vp = struct.unpack('<6f', f.read(24))
            print(f"    View[{wi}]: p=({vp[0]:.3f},{vp[1]:.3f},{vp[2]:.3f}) "
                  f"q=({vp[3]:.3f},{vp[4]:.3f},{vp[5]:.3f})")

        # Check iv[] starts with small integers
        pos = f.tell()
        first_iv = struct.unpack('<4i', f.read(16))
        print(f"    iv[] at {pos}: first 4 = {first_iv}")
        assert first_iv[0] >= 0 and first_iv[0] < 10000, f"iv[0] looks wrong: {first_iv[0]}"

    print(f"    OK")


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(base, 'android', 'app', 'src', 'main', 'assets', 'data', 'map-ckk')

    sol_06 = os.path.join(assets, '06.sol')
    sol_07 = os.path.join(assets, '07.sol')

    if not os.path.exists(sol_06):
        print(f"ERROR: {sol_06} not found")
        sys.exit(1)
    if not os.path.exists(sol_07):
        print(f"ERROR: {sol_07} not found")
        sys.exit(1)

    fix_hole_06(sol_06)
    fix_hole_07(sol_07)

    print(f"\n{'='*60}")
    print("Done. Rebuild with: ./gradlew assemblePuttDebug")


if __name__ == '__main__':
    main()
