#!/usr/bin/env python3
"""
Fix q.sol: rewrite switch section (remove sentinels, fix swch[3]),
remove stale bytes between balls and views.

q.sol has xc=4 switches each preceded by a sentinel pair. The sentinel
consumption shifts subsequent sections. Switch 3's tail data is corrupt
(overlaps with ball data). The correct position for switch 3 comes from
the MAP source (info_camp targeting t1).
"""

import struct, os, sys, shutil

SOL_VERSION_1_6 = 7
M_ALPHA_TEST = 1 << 9
P_ORIENTED = 1
PATHMAX = 64

def read_int(f):
    return struct.unpack('<i', f.read(4))[0]

def read_float(f):
    return struct.unpack('<f', f.read(4))[0]

def skip_to_section(f, target_section):
    """Parse SOL header and skip to the target section.
    Returns (offset, counts_dict)."""

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

    # Skip sections (from fix_sol_balls.py)
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

    if target_section == 'jump':
        return f.tell(), counts

    f.read(jc * 28)
    if target_section == 'switch':
        return f.tell(), counts

    f.read(xc * 40)
    f.read(rc * 88)
    if target_section == 'ball':
        return f.tell(), counts

    return f.tell(), counts


def pack_switch(p, r, pi, t=0.0, t0=0.0, f=0, e=0, i=0):
    """Pack a 40-byte switch entry."""
    return struct.pack('<3f f i f f i i i',
                       p[0], p[1], p[2], r, pi, t, t0, f, e, i)


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    sol_path = os.path.join(base, 'android', 'app', 'src', 'main',
                            'assets', 'data', 'map-paxed', 'q.sol')

    if not os.path.exists(sol_path):
        print(f"ERROR: {sol_path} not found"); sys.exit(1)

    # --- Find switch section offset ---
    with open(sol_path, 'rb') as f:
        switch_offset, c = skip_to_section(f, 'switch')
    jc, xc, rc, uc, wc, ic = c['jc'], c['xc'], c['rc'], c['uc'], c['wc'], c['ic']
    print(f"Header: jc={jc} xc={xc} rc={rc} uc={uc} wc={wc} ic={ic}")
    print(f"Switch section offset: {switch_offset}")

    assert xc == 4
    expected_ball_offset = switch_offset + xc * 40   # 160 bytes for switches
    expected_view_offset = expected_ball_offset + uc * 16

    # --- Read full file ---
    with open(sol_path, 'rb') as f:
        data = bytearray(f.read())
    file_size = len(data)
    print(f"File size: {file_size}")

    # --- Read first 3 switches with sentinel detection ---
    switches = []
    with open(sol_path, 'rb') as f:
        f.seek(switch_offset)
        for si in range(xc):
            pos = f.tell()
            v0 = struct.unpack('<i', f.read(4))[0]
            v1 = struct.unpack('<i', f.read(4))[0]
            sentinel = (v0 == -1 and v1 == -1)
            if not sentinel:
                f.seek(pos)

            body_pos = f.tell()
            p = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            pi = struct.unpack('<i', f.read(4))[0]
            t = struct.unpack('<f', f.read(4))[0]
            t0 = struct.unpack('<f', f.read(4))[0]
            fv = struct.unpack('<i', f.read(4))[0]
            ev = struct.unpack('<i', f.read(4))[0]
            iv = struct.unpack('<i', f.read(4))[0]

            switches.append(dict(p=p, r=r, pi=pi, t=t, t0=t0, f=fv, e=ev, i=iv,
                                 sentinel=sentinel, body_pos=body_pos))
            print(f"  swch[{si}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) r={r:.3f} "
                  f"pi={pi} t={t:.2f} t0={t0:.2f} f={fv} e={ev} i={iv} "
                  f"{'[sentinel]' if sentinel else ''}")

    # --- Determine correct switch 3 values ---
    # From MAP: info_camp at origin (64, 320, 0) targeting t1
    # SOL coords: px=64/64=1.0, py=0/64=0.0, pz=-320/64=-5.0
    # pi: t4→0, t2→2, t3→3, so t1→1
    # Copy t, t0 from a working switch
    ref = switches[0]
    swch3 = dict(
        p=(1.0, 0.0, -5.0),
        r=0.5,
        pi=1,
        t=ref['t'],
        t0=ref['t0'],
        f=0,
        e=0,
        i=0,
    )
    print(f"\n  Fixed swch[3]: p=({swch3['p'][0]:.3f},{swch3['p'][1]:.3f},{swch3['p'][2]:.3f}) "
          f"r={swch3['r']:.3f} pi={swch3['pi']} t={swch3['t']:.2f}")

    # --- Find actual ball and view data in the current file ---
    # Balls: after the sentinel-bearing switch section (switch_offset + 192 bytes)
    actual_switch_end = switches[-1]['body_pos'] + 40
    print(f"\nActual switch section end: {actual_switch_end}")

    # Find ball data: look for uc identical ball entries
    ball_start = actual_switch_end
    ball_data = data[ball_start:ball_start + uc * 16]
    print(f"Ball data at {ball_start}:")
    for bi in range(uc):
        bp = struct.unpack_from('<4f', ball_data, bi * 16)
        print(f"  Ball[{bi}]: p=({bp[0]:.3f},{bp[1]:.3f},{bp[2]:.3f}) r={bp[3]:.4f}")

    # Find view data: scan for valid views after balls + mystery bytes
    view_start = None
    scan_from = ball_start + uc * 16
    scan_to = min(scan_from + 256, file_size - wc * 24)
    for probe in range(scan_from, scan_to, 4):
        ok = True
        for vi in range(wc):
            vp = struct.unpack_from('<6f', data, probe + vi * 24)
            for val in vp:
                if abs(val) > 1000 or val != val:
                    ok = False; break
            if not ok: break
        if ok:
            iv_check = probe + wc * 24
            if iv_check + 8 <= file_size:
                i0, i1 = struct.unpack_from('<2i', data, iv_check)
                if 0 <= i0 < 10000 and 0 <= i1 < 10000:
                    view_start = probe; break

    assert view_start is not None, "Could not find view section"
    mystery_bytes = view_start - (ball_start + uc * 16)
    print(f"View data at {view_start} (mystery gap: {mystery_bytes} bytes)")

    view_data = data[view_start:view_start + wc * 24]
    for vi in range(wc):
        vp = struct.unpack_from('<6f', view_data, vi * 24)
        print(f"  View[{vi}]: p=({vp[0]:.2f},{vp[1]:.2f},{vp[2]:.2f}) "
              f"q=({vp[3]:.2f},{vp[4]:.2f},{vp[5]:.2f})")

    # iv[] data
    iv_start = view_start + wc * 24
    iv_data = data[iv_start:]
    print(f"iv[] at {iv_start}, remaining {len(iv_data)} bytes")

    # --- Build patched file ---
    prefix = data[:switch_offset]

    # Clean switch section (4 entries × 40 bytes, no sentinels)
    new_switches = b''
    for si in range(xc):
        if si < 3:
            sw = switches[si]
            new_switches += pack_switch(sw['p'], sw['r'], sw['pi'],
                                        sw['t'], sw['t0'], sw['f'], sw['e'], sw['i'])
        else:
            new_switches += pack_switch(swch3['p'], swch3['r'], swch3['pi'],
                                        swch3['t'], swch3['t0'], swch3['f'], swch3['e'], swch3['i'])
    assert len(new_switches) == xc * 40

    patched = prefix + new_switches + ball_data + view_data + iv_data

    # --- Backup and write ---
    backup = sol_path + '.bak'
    if not os.path.exists(backup):
        shutil.copy2(sol_path, backup)
        print(f"\nBackup: {backup}")

    with open(sol_path, 'wb') as f:
        f.write(patched)

    new_size = len(patched)
    print(f"\nPatched file: {new_size} bytes (was {file_size}, delta {new_size - file_size})")

    # --- Verify ---
    with open(sol_path, 'rb') as f:
        sw_off2, c2 = skip_to_section(f, 'switch')
        assert sw_off2 == switch_offset

        for si in range(xc):
            p = struct.unpack('<3f', f.read(12))
            r = struct.unpack('<f', f.read(4))[0]
            pi = struct.unpack('<i', f.read(4))[0]
            t = struct.unpack('<f', f.read(4))[0]
            t0 = struct.unpack('<f', f.read(4))[0]
            fv = struct.unpack('<i', f.read(4))[0]
            ev = struct.unpack('<i', f.read(4))[0]
            iv = struct.unpack('<i', f.read(4))[0]
            print(f"  Verify swch[{si}]: p=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) "
                  f"r={r:.3f} pi={pi} t={t:.2f} f={fv} i={iv}")

        for bi in range(uc):
            bp = struct.unpack('<4f', f.read(16))
            print(f"  Verify Ball[{bi}]: ({bp[0]:.3f},{bp[1]:.3f},{bp[2]:.3f}) r={bp[3]:.4f}")

        for wi in range(wc):
            vp = struct.unpack('<6f', f.read(24))
            print(f"  Verify View[{wi}]: p=({vp[0]:.2f},{vp[1]:.2f},{vp[2]:.2f}) "
                  f"q=({vp[3]:.2f},{vp[4]:.2f},{vp[5]:.2f})")

    print("\nDone. Rebuild with: ./gradlew assemblePuttDebug")


if __name__ == '__main__':
    main()
