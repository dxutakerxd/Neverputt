#!/usr/bin/env python3
"""
Diagnose a Neverball/Neverputt SOL binary file section-by-section.

Reads the file exactly as solid_base.c does and tracks the file offset
after every section to detect where extra/garbage bytes appear.
"""

import struct
import sys
import os

SOL_FILE = r"C:\Users\Rog\Documents\aichat\neverputt\drodin-fork\data\map-putt\01_easy.sol"

# Version constants from solid_base.c
SOL_VERSION_1_5 = 6
SOL_VERSION_1_6 = 7
SOL_VERSION_DEV = 8
SOL_VERSION_1_7 = 9
SOL_MAGIC = 0xAF | (ord('S') << 8) | (ord('O') << 16) | (ord('L') << 24)

PATHMAX = 64
M_ALPHA_TEST = (1 << 9)
P_ORIENTED = 1


def read_int(f):
    """Read a 4-byte little-endian signed int (matches get_index)."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(f"Unexpected EOF at offset {f.tell()}")
    return struct.unpack('<i', data)[0]


def read_float(f):
    """Read a 4-byte little-endian float (matches get_float)."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(f"Unexpected EOF at offset {f.tell()}")
    return struct.unpack('<f', data)[0]


def read_array(f, count):
    """Read 'count' little-endian floats (matches get_array)."""
    data = f.read(4 * count)
    if len(data) < 4 * count:
        raise EOFError(f"Unexpected EOF at offset {f.tell()}")
    return struct.unpack(f'<{count}f', data)


def read_raw(f, n):
    """Read n raw bytes."""
    data = f.read(n)
    if len(data) < n:
        raise EOFError(f"Unexpected EOF at offset {f.tell()}")
    return data


def hex_dump_at(f, offset, count=32):
    """Return hex dump of 'count' bytes at given offset without moving cursor."""
    save = f.tell()
    f.seek(offset)
    data = f.read(count)
    f.seek(save)
    hex_str = ' '.join(f'{b:02X}' for b in data)
    return hex_str


def main():
    file_size = os.path.getsize(SOL_FILE)
    print(f"File: {SOL_FILE}")
    print(f"File size: {file_size} bytes")
    print()

    f = open(SOL_FILE, 'rb')

    # ========================== HEADER ==========================
    print("=" * 72)
    print("HEADER")
    print("=" * 72)
    offset_before = f.tell()
    magic = read_int(f)
    version = read_int(f)
    print(f"  Magic:   0x{magic & 0xFFFFFFFF:08X} (expected 0x{SOL_MAGIC:08X}) {'OK' if magic == SOL_MAGIC else 'MISMATCH!'}")
    print(f"  Version: {version}")
    print(f"  Offset after header: {f.tell()}")
    print()

    sol_version = version

    # ========================== INDEX COUNTS ==========================
    print("=" * 72)
    print("INDEX COUNTS")
    print("=" * 72)
    offset_before = f.tell()

    ac = read_int(f)
    dc = read_int(f)
    mc = read_int(f)
    vc = read_int(f)
    ec = read_int(f)
    sc = read_int(f)
    tc = read_int(f)

    oc = 0
    if sol_version >= SOL_VERSION_1_6:
        oc = read_int(f)

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

    counts = {
        'ac': ac, 'dc': dc, 'mc': mc, 'vc': vc, 'ec': ec, 'sc': sc,
        'tc': tc, 'oc': oc, 'gc': gc, 'lc': lc, 'nc': nc, 'pc': pc,
        'bc': bc, 'hc': hc, 'zc': zc, 'jc': jc, 'xc': xc, 'rc': rc,
        'uc': uc, 'wc': wc, 'ic': ic
    }

    for name, val in counts.items():
        print(f"  {name} = {val}")
    print(f"  Offset after index counts: {f.tell()}")
    print()

    # Helper to track and report section boundaries
    cumulative_ok = True

    def section_start(name, expected_offset=None):
        nonlocal cumulative_ok
        actual = f.tell()
        marker = ""
        if expected_offset is not None and actual != expected_offset:
            diff = actual - expected_offset
            marker = f"  *** OFFSET MISMATCH: expected {expected_offset}, got {actual}, diff = {diff:+d} bytes ***"
            cumulative_ok = False
        print(f"--- {name} ---")
        print(f"  Start offset: {actual}{marker}")
        return actual

    def section_end(name, count, expected_size=None):
        actual = f.tell()
        print(f"  End offset:   {actual} (read {count} entries)")
        if expected_size is not None:
            print(f"  Expected size: {expected_size} bytes")
        return actual

    # Track expected offset as we go
    expected_offset = f.tell()

    # ========================== CHAR DATA (av) ==========================
    section_start("CHAR DATA (av)", expected_offset)
    if ac > 0:
        raw_chars = read_raw(f, ac)
        # Show the string data for context
        try:
            decoded = raw_chars.decode('ascii', errors='replace')
            # Show null-separated strings
            strings = decoded.split('\x00')
            strings = [s for s in strings if s]
            print(f"  Strings ({len(strings)}): {strings[:10]}{'...' if len(strings) > 10 else ''}")
        except:
            pass
    section_end("CHAR DATA", ac, ac)
    expected_offset = f.tell()

    # ========================== DICTS (dv) ==========================
    section_start("DICTS (dv)", expected_offset)
    dict_size = 8  # 2 ints
    for i in range(dc):
        ai = read_int(f)
        aj = read_int(f)
    section_end("DICTS", dc, dc * dict_size)
    expected_offset = f.tell()

    # ========================== MATERIALS (mv) ==========================
    section_start("MATERIALS (mv)", expected_offset)
    for i in range(mc):
        mtrl_start = f.tell()
        d = read_array(f, 4)  # diffuse
        a = read_array(f, 4)  # ambient
        s = read_array(f, 4)  # specular
        e = read_array(f, 4)  # emissive
        h = read_array(f, 1)  # shininess
        fl = read_int(f)      # flags
        fname = read_raw(f, PATHMAX)  # texture filename
        fname_str = fname.split(b'\x00')[0].decode('ascii', errors='replace')

        extra = 0
        if sol_version >= SOL_VERSION_1_6:
            if fl & M_ALPHA_TEST:
                alpha_func = read_int(f)
                alpha_ref = read_float(f)
                extra = 8

        mtrl_size = f.tell() - mtrl_start
        print(f"  mtrl[{i}]: fl=0x{fl & 0xFFFFFFFF:08X}, file='{fname_str}', size={mtrl_size} bytes"
              f"{' (has alpha_test +8)' if extra else ''}")
    section_end("MATERIALS", mc)
    expected_offset = f.tell()

    # ========================== VERTS (vv) ==========================
    section_start("VERTS (vv)", expected_offset)
    vert_size = 12  # 3 floats
    for i in range(vc):
        p = read_array(f, 3)
    section_end("VERTS", vc, vc * vert_size)
    expected_offset = f.tell()

    # ========================== EDGES (ev) ==========================
    section_start("EDGES (ev)", expected_offset)
    edge_size = 8  # 2 ints
    for i in range(ec):
        vi = read_int(f)
        vj = read_int(f)
    section_end("EDGES", ec, ec * edge_size)
    expected_offset = f.tell()

    # ========================== SIDES (sv) ==========================
    section_start("SIDES (sv)", expected_offset)
    side_size = 16  # 3 floats + 1 float
    for i in range(sc):
        n = read_array(f, 3)
        d = read_float(f)
    section_end("SIDES", sc, sc * side_size)
    expected_offset = f.tell()

    # ========================== TEXCS (tv) ==========================
    section_start("TEXCS (tv)", expected_offset)
    texc_size = 8  # 2 floats
    for i in range(tc):
        u = read_array(f, 2)
    section_end("TEXCS", tc, tc * texc_size)
    expected_offset = f.tell()

    # ========================== OFFS (ov) ==========================
    if sol_version >= SOL_VERSION_1_6:
        section_start("OFFS (ov)", expected_offset)
        offs_size = 12  # 3 ints
        for i in range(oc):
            ti = read_int(f)
            si = read_int(f)
            vi = read_int(f)
        section_end("OFFS", oc, oc * offs_size)
        expected_offset = f.tell()
    else:
        print("--- OFFS (ov) --- SKIPPED (version < 1.6, oc embedded in geom) ---")

    # ========================== GEOMS (gv) ==========================
    section_start("GEOMS (gv)", expected_offset)
    if sol_version >= SOL_VERSION_1_6:
        geom_size = 16  # 4 ints: mi, oi, oj, ok
        for i in range(gc):
            mi = read_int(f)
            oi = read_int(f)
            oj = read_int(f)
            ok = read_int(f)
    else:
        # version < 1.6: 1 int + 3*(3 ints) = 40 bytes per geom
        geom_size = 40
        for i in range(gc):
            mi = read_int(f)
            for j in range(3):
                ti = read_int(f)
                si = read_int(f)
                vi = read_int(f)
    section_end("GEOMS", gc, gc * geom_size)
    expected_offset = f.tell()

    # ========================== LUMPS (lv) ==========================
    section_start("LUMPS (lv)", expected_offset)
    lump_size = 36  # 9 ints
    for i in range(lc):
        fl = read_int(f)
        v0 = read_int(f)
        _vc = read_int(f)
        e0 = read_int(f)
        _ec = read_int(f)
        g0 = read_int(f)
        _gc = read_int(f)
        s0 = read_int(f)
        _sc = read_int(f)
    section_end("LUMPS", lc, lc * lump_size)
    expected_offset = f.tell()

    # ========================== NODES (nv) ==========================
    section_start("NODES (nv)", expected_offset)
    node_size = 20  # 5 ints: si, ni, nj, l0, lc
    for i in range(nc):
        si = read_int(f)
        ni = read_int(f)
        nj = read_int(f)
        l0 = read_int(f)
        _lc = read_int(f)
    section_end("NODES", nc, nc * node_size)
    expected_offset = f.tell()

    # ========================== PATHS (pv) ==========================
    section_start("PATHS (pv)", expected_offset)
    for i in range(pc):
        path_start = f.tell()
        p = read_array(f, 3)   # p[3]
        t = read_float(f)      # t
        pi = read_int(f)       # pi
        path_f = read_int(f)   # f
        path_s = read_int(f)   # s

        path_fl = 0
        if sol_version >= SOL_VERSION_1_6:
            path_fl = read_int(f)  # fl

        if path_fl & P_ORIENTED:
            e = read_array(f, 4)  # e[4] quaternion

        path_size = f.tell() - path_start
        print(f"  path[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), t={t:.4f}, pi={pi}, f={path_f}, s={path_s}, fl={path_fl}, size={path_size}")
    section_end("PATHS", pc)
    expected_offset = f.tell()

    # ========================== BODIES (bv) ==========================
    section_start("BODIES (bv)", expected_offset)
    for i in range(bc):
        body_start = f.tell()
        bpi = read_int(f)  # pi

        bpj = bpi
        if sol_version >= SOL_VERSION_1_6:
            bpj = read_int(f)  # pj
            if bpj < 0:
                bpj = bpi

        bni = read_int(f)  # ni
        bl0 = read_int(f)  # l0
        blc = read_int(f)  # lc
        bg0 = read_int(f)  # g0
        bgc = read_int(f)  # gc

        body_size = f.tell() - body_start
        print(f"  body[{i}]: pi={bpi}, pj={bpj}, ni={bni}, l0={bl0}, lc={blc}, g0={bg0}, gc={bgc}, size={body_size}")
    section_end("BODIES", bc)
    expected_offset = f.tell()

    # ========================== ITEMS (hv) ==========================
    section_start("ITEMS (hv)", expected_offset)
    item_size = 20  # 3 floats + 2 ints
    for i in range(hc):
        p = read_array(f, 3)
        t = read_int(f)
        n = read_int(f)
        print(f"  item[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), t={t}, n={n}")
    section_end("ITEMS", hc, hc * item_size)
    expected_offset = f.tell()

    # ========================== GOALS (zv) ==========================
    section_start("GOALS (zv)", expected_offset)
    goal_size = 16  # 3 floats + 1 float
    for i in range(zc):
        p = read_array(f, 3)
        r = read_float(f)
        print(f"  goal[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), r={r:.2f}")
    section_end("GOALS", zc, zc * goal_size)
    expected_offset = f.tell()

    # ========================== CHECK FOR GARBAGE BEFORE JUMPS ==========================
    print()
    print("=" * 72)
    print("GARBAGE CHECK BEFORE JUMPS")
    print("=" * 72)
    print(f"  Current offset (end of goals): {f.tell()}")
    print(f"  jc = {jc}")

    if jc > 0:
        # Peek at next 16 bytes
        peek_offset = f.tell()
        peek_data = f.read(min(32, file_size - peek_offset))
        f.seek(peek_offset)  # rewind
        print(f"  Next 32 bytes at offset {peek_offset}:")
        for i in range(0, len(peek_data), 4):
            chunk = peek_data[i:i+4]
            if len(chunk) == 4:
                as_int = struct.unpack('<i', chunk)[0]
                as_uint = struct.unpack('<I', chunk)[0]
                as_float = struct.unpack('<f', chunk)[0]
                print(f"    +{i:3d}: 0x{as_uint:08X}  int={as_int:12d}  float={as_float:15.6f}")

        # Check for 0xFFFFFFFF pattern
        v0_bytes = f.read(4)
        v1_bytes = f.read(4)
        f.seek(peek_offset)  # rewind again

        v0 = struct.unpack('<i', v0_bytes)[0]
        v1 = struct.unpack('<i', v1_bytes)[0]

        if v0 == -1 and v1 == -1:
            print(f"\n  *** FOUND 2 GARBAGE 0xFFFFFFFF VALUES at offset {peek_offset} ***")
            print(f"  These are the 2 extra bytes (8 bytes total) that corrupt the file!")
            print(f"  Without skipping them, jump data would be misaligned by 8 bytes.")
            # Skip them like the C code does
            f.seek(peek_offset + 8)
        else:
            print(f"\n  No garbage 0xFFFFFFFF pattern found at offset {peek_offset}.")
            print(f"  v0 = 0x{v0 & 0xFFFFFFFF:08X}, v1 = 0x{v1 & 0xFFFFFFFF:08X}")

    expected_offset = f.tell()

    # ========================== JUMPS (jv) ==========================
    print()
    section_start("JUMPS (jv)", expected_offset)
    jump_size = 28  # 3 floats + 3 floats + 1 float
    for i in range(jc):
        p = read_array(f, 3)
        q = read_array(f, 3)
        r = read_float(f)
        print(f"  jump[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), q=({q[0]:.2f},{q[1]:.2f},{q[2]:.2f}), r={r:.2f}")
    section_end("JUMPS", jc, jc * jump_size)
    expected_offset = f.tell()

    # ========================== SWITCHES (xv) ==========================
    section_start("SWITCHES (xv)", expected_offset)
    swch_size = 36  # 3f + 1f + 1i + 2f + 2i + 1i = 12+4+4+8+8+4 = 40? Let me recount
    # p[3] = 12, r = 4, pi = 4, t = 4, (void)t = 4, f = 4, (void)f = 4, i = 4 = 40
    swch_size = 40
    for i in range(xc):
        p = read_array(f, 3)
        r = read_float(f)
        xpi = read_int(f)
        xt = read_float(f)
        _xt2 = read_float(f)  # (void) duplicate
        xf = read_int(f)
        _xf2 = read_int(f)    # (void) duplicate
        xi = read_int(f)
        print(f"  swch[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), r={r:.2f}, pi={xpi}, t={xt:.4f}, f={xf}, i={xi}")
    section_end("SWITCHES", xc, xc * swch_size)
    expected_offset = f.tell()

    # ========================== BILLBOARDS (rv) ==========================
    section_start("BILLBOARDS (rv)", expected_offset)
    # 2 ints + 2 floats + 6*3 floats = 8 + 8 + 72 = 88 bytes
    bill_size = 88
    for i in range(rc):
        bfl = read_int(f)
        bmi = read_int(f)
        bt = read_float(f)
        bd = read_float(f)
        w = read_array(f, 3)
        h = read_array(f, 3)
        rx = read_array(f, 3)
        ry = read_array(f, 3)
        rz = read_array(f, 3)
        bp = read_array(f, 3)
        print(f"  bill[{i}]: fl={bfl}, mi={bmi}, t={bt:.4f}, d={bd:.4f}")
    section_end("BILLBOARDS", rc, rc * bill_size)
    expected_offset = f.tell()

    # ========================== BALLS (uv) ==========================
    section_start("BALLS (uv)", expected_offset)
    ball_size = 16  # 3 floats + 1 float
    for i in range(uc):
        p = read_array(f, 3)
        r = read_float(f)
        print(f"  ball[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), r={r:.2f}")
    section_end("BALLS", uc, uc * ball_size)
    expected_offset = f.tell()

    # ========================== VIEWS (wv) ==========================
    section_start("VIEWS (wv)", expected_offset)
    view_size = 24  # 3 floats + 3 floats
    for i in range(wc):
        p = read_array(f, 3)
        q = read_array(f, 3)
        print(f"  view[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), q=({q[0]:.2f},{q[1]:.2f},{q[2]:.2f})")
    section_end("VIEWS", wc, wc * view_size)
    expected_offset = f.tell()

    # ========================== INDEX ARRAY (iv) ==========================
    section_start("INDEX ARRAY (iv)", expected_offset)
    idx_size = 4  # 1 int each
    for i in range(ic):
        iv_val = read_int(f)
        if i < 10 or i >= ic - 5:
            print(f"  iv[{i}] = {iv_val}")
        elif i == 10:
            print(f"  ... ({ic - 15} more entries) ...")
    section_end("INDEX ARRAY", ic, ic * idx_size)

    # ========================== FINAL STATUS ==========================
    remaining = file_size - f.tell()
    print()
    print("=" * 72)
    print("FINAL STATUS")
    print("=" * 72)
    print(f"  File size:          {file_size}")
    print(f"  Current offset:     {f.tell()}")
    print(f"  Remaining bytes:    {remaining}")

    if remaining > 0:
        print(f"\n  *** {remaining} EXTRA BYTES at end of file ***")
        extra_data = f.read(min(remaining, 64))
        print(f"  Hex dump of remaining bytes:")
        for i in range(0, len(extra_data), 4):
            chunk = extra_data[i:i+4]
            if len(chunk) == 4:
                as_int = struct.unpack('<i', chunk)[0]
                as_uint = struct.unpack('<I', chunk)[0]
                as_float = struct.unpack('<f', chunk)[0]
                print(f"    +{i:3d}: 0x{as_uint:08X}  int={as_int:12d}  float={as_float:15.6f}")
            else:
                print(f"    +{i:3d}: {' '.join(f'{b:02X}' for b in chunk)}")
    elif remaining == 0:
        print(f"\n  File consumed exactly - no extra bytes.")
    else:
        print(f"\n  *** READ PAST END OF FILE by {-remaining} bytes ***")

    # ========================== ALSO: Try reading WITHOUT skipping garbage ==========================
    print()
    print("=" * 72)
    print("VERIFICATION: What happens WITHOUT garbage skip")
    print("=" * 72)

    f.seek(0)
    # Re-read to the goals end point
    # We know the offset from above - let's be precise
    # Re-parse up to goals end
    f.seek(0)
    read_int(f)  # magic
    read_int(f)  # version

    # Skip index counts
    idx_count = 20 if sol_version < SOL_VERSION_1_6 else 21
    for _ in range(idx_count):
        read_int(f)

    # Skip char data
    f.read(ac)

    # Skip dicts
    for _ in range(dc):
        read_int(f); read_int(f)

    # Skip materials (variable size - re-parse)
    for i in range(mc):
        read_array(f, 4)
        read_array(f, 4)
        read_array(f, 4)
        read_array(f, 4)
        read_array(f, 1)
        fl = read_int(f)
        read_raw(f, PATHMAX)
        if sol_version >= SOL_VERSION_1_6 and (fl & M_ALPHA_TEST):
            read_int(f)
            read_float(f)

    # Skip verts
    for _ in range(vc):
        read_array(f, 3)

    # Skip edges
    for _ in range(ec):
        read_int(f); read_int(f)

    # Skip sides
    for _ in range(sc):
        read_array(f, 3); read_float(f)

    # Skip texcs
    for _ in range(tc):
        read_array(f, 2)

    # Skip offs
    if sol_version >= SOL_VERSION_1_6:
        for _ in range(oc):
            read_int(f); read_int(f); read_int(f)

    # Skip geoms
    if sol_version >= SOL_VERSION_1_6:
        for _ in range(gc):
            read_int(f); read_int(f); read_int(f); read_int(f)
    else:
        for _ in range(gc):
            read_int(f)
            for j in range(3):
                read_int(f); read_int(f); read_int(f)

    # Skip lumps
    for _ in range(lc):
        for __ in range(9):
            read_int(f)

    # Skip nodes
    for _ in range(nc):
        for __ in range(5):
            read_int(f)

    # Skip paths
    for i in range(pc):
        read_array(f, 3)
        read_float(f)
        read_int(f); read_int(f); read_int(f)
        path_fl = 0
        if sol_version >= SOL_VERSION_1_6:
            path_fl = read_int(f)
        if path_fl & P_ORIENTED:
            read_array(f, 4)

    # Skip bodies
    for _ in range(bc):
        read_int(f)
        if sol_version >= SOL_VERSION_1_6:
            read_int(f)
        read_int(f); read_int(f); read_int(f); read_int(f); read_int(f)

    # Skip items
    for _ in range(hc):
        read_array(f, 3); read_int(f); read_int(f)

    # Skip goals
    for _ in range(zc):
        read_array(f, 3); read_float(f)

    goals_end = f.tell()
    print(f"  Offset at end of goals section: {goals_end}")

    # Now try reading jumps WITHOUT skipping garbage
    print(f"\n  Reading {jc} jumps WITHOUT garbage skip:")
    for i in range(jc):
        p = read_array(f, 3)
        q = read_array(f, 3)
        r = read_float(f)
        print(f"    jump[{i}]: p=({p[0]:.6f},{p[1]:.6f},{p[2]:.6f}), q=({q[0]:.6f},{q[1]:.6f},{q[2]:.6f}), r={r:.6f}")
        # Check for NaN
        import math
        vals = list(p) + list(q) + [r]
        if any(math.isnan(v) or math.isinf(v) for v in vals):
            print(f"    *** Contains NaN/Inf - DATA IS CORRUPTED ***")

    remaining_no_skip = file_size - f.tell()
    print(f"\n  Remaining bytes after jumps+rest (no skip): {remaining_no_skip}")
    print(f"  Current offset: {f.tell()}")

    # Continue reading remaining sections without skip to show cascading damage
    print(f"\n  Reading {xc} switches (cascading from no-skip):")
    for i in range(xc):
        try:
            p = read_array(f, 3)
            r = read_float(f)
            xpi = read_int(f)
            xt = read_float(f)
            _xt2 = read_float(f)
            xf = read_int(f)
            _xf2 = read_int(f)
            xi = read_int(f)
            print(f"    swch[{i}]: p=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f}), r={r:.2f}, pi={xpi}")
        except EOFError as e:
            print(f"    swch[{i}]: *** EOF - ran out of data ***")
            break

    f.close()
    print()
    print("Done.")


if __name__ == '__main__':
    main()
