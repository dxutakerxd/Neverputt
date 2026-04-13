#!/usr/bin/env python3
"""
Fix map-ckk hole 12: remove 2 jump + 5 switch sentinels, fix Switch[4] tail
and Switch[5] (completely corrupted), fix balls and views.

Root cause: fix_sol_balls.py wrote ball data 56 bytes too early (not accounting
for 7 sentinel pairs), overwriting Switch[4]'s t0/f/e/i, all of Switch[5],
and shifting ball/view data.
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
    """Parse SOL header and skip to end of goal section."""
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
    f.read(zc * 16)

    return f.tell(), counts


def pack_jump(p, q, r):
    return struct.pack('<7f', p[0], p[1], p[2], q[0], q[1], q[2], r)


def pack_switch(p, r, pi, t=0.0, t0=0.0, f=0, e=0, i=0):
    return struct.pack('<3f f i f f i i i', p[0], p[1], p[2], r, pi, t, t0, f, e, i)


def pack_ball(p, r):
    return struct.pack('<4f', p[0], p[1], p[2], r)


def pack_view(p, q):
    return struct.pack('<6f', p[0], p[1], p[2], q[0], q[1], q[2])


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    sol_path = os.path.join(base, 'android', 'app', 'src', 'main',
                            'assets', 'data', 'map-ckk', '12.sol')

    if not os.path.exists(sol_path):
        print(f"ERROR: {sol_path} not found")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"Fixing hole 12: {sol_path}")

    # === Correct values from 12.map ===

    # Jump[0] (e28): origin=(-448,-32,-16) target=t4->e23:(200,0,248)
    # Jump[1] (e29): origin=(448,-32,-16) target=t3->e22:(-200,0,248)
    jumps = [
        ((-7.0, -0.25, 0.5), (3.125, 3.875, 0.0), 0.5),
        ((7.0, -0.25, 0.5), (-3.125, 3.875, 0.0), 0.5),
    ]

    # Switches (6 info_camp, sorted by entity number = SOL order)
    # Path index mapping from entity order:
    #   e12:p1_0->path[0], e13:p1_5->path[1], e14:p1_4->path[2],
    #   e15:p1_3->path[3], e16:p1_2->path[4], e17:p1_1->path[5]
    switches = [
        # Swch[0] (e6): origin=(-416,144,-16) target=p1_5->path[1]
        ((-6.5, -0.25, -2.25), 0.5, 1),
        # Swch[1] (e7): origin=(352,288,-16) target=p1_0->path[0]
        ((5.5, -0.25, -4.5), 0.5, 0),
        # Swch[2] (e8): origin=(144,368,-16) target=p1_1->path[5]
        ((2.25, -0.25, -5.75), 0.5, 5),
        # Swch[3] (e9): origin=(-192,432,-16) target=p1_2->path[4]
        ((-3.0, -0.25, -6.75), 0.5, 4),
        # Swch[4] (e10): origin=(-384,336,-16) target=p1_3->path[3]
        ((-6.0, -0.25, -5.25), 0.5, 3),
        # Swch[5] (e11): origin=(-272,224,-16) target=p1_4->path[2]
        ((-4.25, -0.25, -3.5), 0.5, 2),
    ]

    # Ball: origin=(0,0,24) r=0.0625 -> (0, (24-24)/64+0.0625+0.0005, 0)
    ball = ((0.0, 0.063, 0.0), 0.0625)

    # View[0] (e24): origin=(-855.5,903.5,893) target=t1->e25:(63,-36.25,-175.625)
    # View[1] (e26): origin=(-499,-64,-11) target=t2->e27:(-263,-241,45)
    views = [
        ((-855.5/64, 893/64, -903.5/64), (63/64, -175.625/64, 36.25/64)),
        ((-499/64, -11/64, 64/64), (-263/64, 45/64, 241/64)),
    ]

    # === Parse file ===
    with open(sol_path, 'rb') as f:
        goal_end, c = skip_to_goal_end(f)

    jc, xc, rc, uc, wc, ic = c['jc'], c['xc'], c['rc'], c['uc'], c['wc'], c['ic']
    print(f"  Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc} ic={ic}")
    assert jc == 2 and xc == 6 and rc == 0 and uc == 5 and wc == 2

    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())
    file_size = len(data)
    iv_start = file_size - ic * 4

    old_region_size = iv_start - goal_end
    new_region_size = jc * 28 + xc * 40 + uc * 16 + wc * 24
    print(f"  Goal end: {goal_end}, iv start: {iv_start}")
    print(f"  Region: {old_region_size} -> {new_region_size} bytes")

    # === Diagnostics ===
    pos = goal_end
    sentinels = 0
    for ji in range(jc):
        v0, v1 = struct.unpack_from('<2i', data, pos)
        if v0 == -1 and v1 == -1:
            sentinels += 1
            pos += 8
        jp = struct.unpack_from('<3f', data, pos)
        jr = struct.unpack_from('<f', data, pos + 24)[0]
        print(f"    Jump[{ji}]: p=({jp[0]:.3f},{jp[1]:.3f},{jp[2]:.3f}) r={jr:.3f}")
        pos += 28

    for xi in range(xc):
        v0, v1 = struct.unpack_from('<2i', data, pos)
        if v0 == -1 and v1 == -1:
            sentinels += 1
            pos += 8
        sp = struct.unpack_from('<3f', data, pos)
        sr = struct.unpack_from('<f', data, pos + 12)[0]
        spi = struct.unpack_from('<i', data, pos + 16)[0]
        sf = struct.unpack_from('<i', data, pos + 28)[0]
        si = struct.unpack_from('<i', data, pos + 36)[0]
        exp = switches[xi]
        p_ok = all(abs(sp[i] - exp[0][i]) < 0.02 for i in range(3))
        pi_ok = spi == exp[2]
        fi_ok = sf == 0 and si == 0
        status = 'OK' if (p_ok and pi_ok and fi_ok) else '** FIX'
        print(f"    Swch[{xi}]: p=({sp[0]:.3f},{sp[1]:.3f},{sp[2]:.3f}) "
              f"r={sr:.3f} pi={spi} f={sf} i={si} {status}")
        pos += 40

    print(f"  Sentinels: {sentinels}")

    # === Build clean region ===
    new_region = b''
    for p, q, r in jumps:
        new_region += pack_jump(p, q, r)
    for p, r, pi in switches:
        new_region += pack_switch(p, r, pi)
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
            t = struct.unpack('<f', f.read(4))[0]
            t0 = struct.unpack('<f', f.read(4))[0]
            fv = struct.unpack('<i', f.read(4))[0]
            ev = struct.unpack('<i', f.read(4))[0]
            iv = struct.unpack('<i', f.read(4))[0]
            print(f"    Swch[{xi}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) "
                  f"r={r:.3f} pi={pi} t={t:.2f} f={fv} e={ev} i={iv}")

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
    print(f"\n{'='*60}")
    print("Done. Rebuild with: ./gradlew assemblePuttDebug")


if __name__ == '__main__':
    main()
