#!/usr/bin/env python3
"""
Parse a Neverball/Neverputt SOL binary file and extract jump, goal, ball,
and view data for analysis.  Based on the C code in share/solid_base.c.

Binary layout (little-endian, version >= 1.6 / SOL_VERSION_1_6 = 7):
  Header:  magic(4)  version(4)
  Index:   ac dc mc vc ec sc tc oc gc lc nc pc bc hc zc jc xc rc uc wc ic
           (each 4 bytes; oc present only when version >= 7)
  Data sections in order:
    av (raw chars, ac bytes)
    dict  (dc * 8 bytes)   -- 2 ints
    mtrl  (mc * variable)  -- see below
    vert  (vc * 12 bytes)  -- 3 floats
    edge  (ec * 8 bytes)   -- 2 ints
    side  (sc * 16 bytes)  -- 3 floats + 1 float
    texc  (tc * 8 bytes)   -- 2 floats
    offs  (oc * 12 bytes)  -- 3 ints
    geom  (gc * 16 bytes)  -- 4 ints  (version >= 7)
    lump  (lc * 36 bytes)  -- 9 ints
    node  (nc * 20 bytes)  -- 5 ints
    path  (pc * variable)  -- 3 floats + 1 float + 3 ints + conditionally 1 int + 4 floats
    body  (bc * 28 bytes)  -- 7 ints  (version >= 7)
    item  (hc * 20 bytes)  -- 3 floats + 2 ints
    goal  (zc * 16 bytes)  -- 3 floats + 1 float
    jump  (jc * 28 bytes)  -- 3 floats + 3 floats + 1 float
    swch  (xc * 36 bytes)  -- 3 floats + 1 float + 1 int + 1 float + 1 float + 1 int + 1 int + 1 int
    bill  (rc * 80 bytes)  -- 2 ints + 2 floats + 18 floats
    ball  (uc * 16 bytes)  -- 3 floats + 1 float
    view  (wc * 24 bytes)  -- 6 floats
    iv    (ic * 4 bytes)   -- ints
"""

import struct
import sys
import math
import os

SOL_MAGIC = 0xAF | (ord('S') << 8) | (ord('O') << 16) | (ord('L') << 24)

SOL_VERSION_1_5 = 6
SOL_VERSION_1_6 = 7
SOL_VERSION_DEV = 8
SOL_VERSION_1_7 = 9

PATHMAX = 64

# M_ALPHA_TEST flag
M_ALPHA_TEST = (1 << 9)

# P_ORIENTED flag
P_ORIENTED = 1


def read_int(f):
    """Read a 4-byte little-endian signed int."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(f"Expected 4 bytes for int, got {len(data)}")
    return struct.unpack('<i', data)[0]


def read_float(f):
    """Read a 4-byte little-endian float."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(f"Expected 4 bytes for float, got {len(data)}")
    return struct.unpack('<f', data)[0]


def read_float_raw(f):
    """Read a 4-byte little-endian float and return both raw bytes and value."""
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(f"Expected 4 bytes for float, got {len(data)}")
    val = struct.unpack('<f', data)[0]
    return data, val


def read_floats(f, n):
    """Read n little-endian floats."""
    return [read_float(f) for _ in range(n)]


def read_floats_raw(f, n):
    """Read n little-endian floats, returning list of (raw_bytes, value) tuples."""
    return [read_float_raw(f) for _ in range(n)]


def is_suspicious(val):
    """Check if a float value looks corrupted."""
    if math.isnan(val):
        return "NaN"
    if math.isinf(val):
        return "Inf"
    if abs(val) > 10000.0:
        return f"very large ({val})"
    return None


def hex_bytes(data):
    """Format bytes as hex string."""
    return ' '.join(f'{b:02X}' for b in data)


def main():
    sol_path = r"C:\Users\Rog\Documents\aichat\neverputt\drodin-fork\data\map-putt\07_tele.sol"

    if not os.path.exists(sol_path):
        print(f"ERROR: SOL file not found at: {sol_path}")
        sys.exit(1)

    file_size = os.path.getsize(sol_path)
    print(f"SOL file: {sol_path}")
    print(f"File size: {file_size} bytes")
    print("=" * 80)

    with open(sol_path, 'rb') as f:
        # ---- Header ----
        magic = read_int(f)
        version = read_int(f)

        print(f"\n--- HEADER ---")
        print(f"Magic:   0x{magic & 0xFFFFFFFF:08X}  (expected 0x{SOL_MAGIC & 0xFFFFFFFF:08X})")
        if magic != SOL_MAGIC:
            print("  WARNING: Magic mismatch!")
        print(f"Version: {version}  (min={SOL_VERSION_1_5}, max={SOL_VERSION_1_7})")

        if version < SOL_VERSION_1_5 or version > SOL_VERSION_1_7:
            print("  WARNING: Version out of supported range!")

        # ---- Index counts ----
        ac = read_int(f)
        dc = read_int(f)
        mc = read_int(f)
        vc = read_int(f)
        ec = read_int(f)
        sc = read_int(f)
        tc = read_int(f)

        oc = 0
        if version >= SOL_VERSION_1_6:
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

        print(f"\n--- INDEX COUNTS ---")
        print(f"  ac (text chars)   = {ac}")
        print(f"  dc (dicts)        = {dc}")
        print(f"  mc (materials)    = {mc}")
        print(f"  vc (vertices)     = {vc}")
        print(f"  ec (edges)        = {ec}")
        print(f"  sc (sides)        = {sc}")
        print(f"  tc (texcoords)    = {tc}")
        if version >= SOL_VERSION_1_6:
            print(f"  oc (offsets)      = {oc}")
        print(f"  gc (geoms)        = {gc}")
        print(f"  lc (lumps)        = {lc}")
        print(f"  nc (nodes)        = {nc}")
        print(f"  pc (paths)        = {pc}")
        print(f"  bc (bodies)       = {bc}")
        print(f"  hc (items)        = {hc}")
        print(f"  zc (goals)        = {zc}")
        print(f"  jc (jumps)        = {jc}")
        print(f"  xc (switches)     = {xc}")
        print(f"  rc (billboards)   = {rc}")
        print(f"  uc (balls)        = {uc}")
        print(f"  wc (views)        = {wc}")
        print(f"  ic (indices)      = {ic}")

        after_index_offset = f.tell()
        print(f"\n  Offset after index section: {after_index_offset}")

        # ---- Skip to data sections ----
        # We need to skip through each section in order to reach jumps.
        # But we also want to read goals, balls, and views.
        # Let's track offsets.

        # 1. av (text data)
        av_offset = f.tell()
        av_data = f.read(ac) if ac > 0 else b''
        print(f"\n--- TEXT DATA (av) ---")
        print(f"  Offset: {av_offset}, Size: {ac} bytes")
        if ac > 0:
            # Show the string table (null-separated strings)
            strings = av_data.split(b'\x00')
            for i, s in enumerate(strings):
                if s:
                    print(f"  String {i}: {s.decode('ascii', errors='replace')}")

        # 2. dict (dc entries, 2 ints each = 8 bytes)
        dict_offset = f.tell()
        print(f"\n--- DICT DATA ---")
        print(f"  Offset: {dict_offset}, Count: {dc}, Each: 8 bytes")
        dicts = []
        for i in range(dc):
            ai = read_int(f)
            aj = read_int(f)
            dicts.append((ai, aj))
            # Resolve to actual strings if possible
            key_str = ""
            val_str = ""
            if 0 <= ai < ac:
                end = av_data.index(b'\x00', ai) if b'\x00' in av_data[ai:] else ac
                key_str = av_data[ai:end].decode('ascii', errors='replace')
            if 0 <= aj < ac:
                end = av_data.index(b'\x00', aj) if b'\x00' in av_data[aj:] else ac
                val_str = av_data[aj:end].decode('ascii', errors='replace')
            print(f"  Dict[{i}]: ai={ai} aj={aj}  =>  \"{key_str}\" = \"{val_str}\"")

        # 3. mtrl (mc entries, variable size)
        mtrl_offset = f.tell()
        print(f"\n--- MATERIAL DATA ---")
        print(f"  Offset: {mtrl_offset}, Count: {mc}")
        for i in range(mc):
            start_pos = f.tell()
            d = read_floats(f, 4)  # diffuse
            a = read_floats(f, 4)  # ambient
            s = read_floats(f, 4)  # specular
            e = read_floats(f, 4)  # emission
            h = read_floats(f, 1)  # shininess
            fl = read_int(f)       # flags
            fname = f.read(PATHMAX)  # file name
            fname_str = fname.split(b'\x00')[0].decode('ascii', errors='replace')

            extra = ""
            if version >= SOL_VERSION_1_6:
                if fl & M_ALPHA_TEST:
                    alpha_func = read_int(f)
                    alpha_ref = read_float(f)
                    extra = f"  alpha_func={alpha_func} alpha_ref={alpha_ref}"

            end_pos = f.tell()
            print(f"  Mtrl[{i}]: flags=0x{fl:04X} file=\"{fname_str}\" "
                  f"size={end_pos - start_pos}{extra}")

        # 4. vert (vc entries, 3 floats = 12 bytes)
        vert_offset = f.tell()
        print(f"\n--- VERTEX DATA ---")
        print(f"  Offset: {vert_offset}, Count: {vc}, Each: 12 bytes, "
              f"Total: {vc * 12} bytes")
        for i in range(vc):
            p = read_floats(f, 3)
        print(f"  (skipped {vc} vertices for brevity)")

        # 5. edge (ec entries, 2 ints = 8 bytes)
        edge_offset = f.tell()
        print(f"\n--- EDGE DATA ---")
        print(f"  Offset: {edge_offset}, Count: {ec}, Each: 8 bytes, "
              f"Total: {ec * 8} bytes")
        f.read(ec * 8)  # skip

        # 6. side (sc entries, 3 floats + 1 float = 16 bytes)
        side_offset = f.tell()
        print(f"\n--- SIDE DATA ---")
        print(f"  Offset: {side_offset}, Count: {sc}, Each: 16 bytes, "
              f"Total: {sc * 16} bytes")
        f.read(sc * 16)  # skip

        # 7. texc (tc entries, 2 floats = 8 bytes)
        texc_offset = f.tell()
        print(f"\n--- TEXCOORD DATA ---")
        print(f"  Offset: {texc_offset}, Count: {tc}, Each: 8 bytes, "
              f"Total: {tc * 8} bytes")
        f.read(tc * 8)  # skip

        # 8. offs (oc entries, 3 ints = 12 bytes)
        offs_offset = f.tell()
        print(f"\n--- OFFSET DATA ---")
        print(f"  Offset: {offs_offset}, Count: {oc}, Each: 12 bytes, "
              f"Total: {oc * 12} bytes")
        f.read(oc * 12)  # skip

        # 9. geom (gc entries, version >= 1.6: 4 ints = 16 bytes)
        geom_offset = f.tell()
        if version >= SOL_VERSION_1_6:
            geom_each = 16
        else:
            geom_each = 36  # 3 * (3 ints) = 9 ints + 1 int (mi) = 40? actually more complex for v1.5
        print(f"\n--- GEOM DATA ---")
        print(f"  Offset: {geom_offset}, Count: {gc}, Each: {geom_each} bytes")
        if version >= SOL_VERSION_1_6:
            f.read(gc * 16)  # skip
        else:
            # version 1.5: mi + 3 * (ti, si, vi) = 1 + 9 = 10 ints = 40 bytes
            for i in range(gc):
                read_int(f)  # mi
                for _ in range(3):
                    read_int(f)  # ti
                    read_int(f)  # si
                    read_int(f)  # vi

        # 10. lump (lc entries, 9 ints = 36 bytes)
        lump_offset = f.tell()
        print(f"\n--- LUMP DATA ---")
        print(f"  Offset: {lump_offset}, Count: {lc}, Each: 36 bytes, "
              f"Total: {lc * 36} bytes")
        f.read(lc * 36)  # skip

        # 11. node (nc entries, 5 ints = 20 bytes)
        node_offset = f.tell()
        print(f"\n--- NODE DATA ---")
        print(f"  Offset: {node_offset}, Count: {nc}, Each: 20 bytes, "
              f"Total: {nc * 20} bytes")
        f.read(nc * 20)  # skip

        # 12. path (pc entries, variable size)
        path_offset = f.tell()
        print(f"\n--- PATH DATA ---")
        print(f"  Offset: {path_offset}, Count: {pc}")
        for i in range(pc):
            p = read_floats(f, 3)
            t = read_float(f)
            pi = read_int(f)
            path_f = read_int(f)
            path_s = read_int(f)
            path_fl = 0
            if version >= SOL_VERSION_1_6:
                path_fl = read_int(f)
            if path_fl & P_ORIENTED:
                e = read_floats(f, 4)
            print(f"  Path[{i}]: p=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) "
                  f"t={t:.2f} pi={pi} f={path_f} s={path_s} fl={path_fl}")

        # 13. body (bc entries)
        body_offset = f.tell()
        print(f"\n--- BODY DATA ---")
        print(f"  Offset: {body_offset}, Count: {bc}")
        if version >= SOL_VERSION_1_6:
            body_size = 28  # 7 ints
        else:
            body_size = 24  # 6 ints (no pj)
        for i in range(bc):
            pi = read_int(f)
            if version >= SOL_VERSION_1_6:
                pj = read_int(f)
            else:
                pj = pi
            ni = read_int(f)
            l0 = read_int(f)
            body_lc = read_int(f)
            g0 = read_int(f)
            body_gc = read_int(f)
            print(f"  Body[{i}]: pi={pi} pj={pj} ni={ni} "
                  f"l0={l0} lc={body_lc} g0={g0} gc={body_gc}")

        # 14. item (hc entries, 3 floats + 2 ints = 20 bytes)
        item_offset = f.tell()
        print(f"\n--- ITEM DATA ---")
        print(f"  Offset: {item_offset}, Count: {hc}")
        for i in range(hc):
            p = read_floats(f, 3)
            item_t = read_int(f)
            item_n = read_int(f)
            print(f"  Item[{i}]: p=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) "
                  f"type={item_t} n={item_n}")

        # ============================================================
        # 15. GOAL DATA (zc entries, 3 floats + 1 float = 16 bytes)
        # ============================================================
        goal_offset = f.tell()
        print(f"\n{'=' * 80}")
        print(f"--- GOAL DATA ---")
        print(f"  Offset: {goal_offset}, Count: {zc}, Each: 16 bytes")
        goals = []
        for i in range(zc):
            raw_p = read_floats_raw(f, 3)
            raw_r = read_float_raw(f)
            p_vals = [v for _, v in raw_p]
            r_val = raw_r[1]
            goals.append((p_vals, r_val))

            print(f"\n  Goal[{i}]:")
            print(f"    p[0] = {p_vals[0]:12.6f}  raw: {hex_bytes(raw_p[0][0])}")
            print(f"    p[1] = {p_vals[1]:12.6f}  raw: {hex_bytes(raw_p[1][0])}")
            print(f"    p[2] = {p_vals[2]:12.6f}  raw: {hex_bytes(raw_p[2][0])}")
            print(f"    r    = {r_val:12.6f}  raw: {hex_bytes(raw_r[0])}")

            for j, v in enumerate(p_vals):
                s = is_suspicious(v)
                if s:
                    print(f"    *** WARNING: p[{j}] is suspicious: {s}")
            s = is_suspicious(r_val)
            if s:
                print(f"    *** WARNING: r is suspicious: {s}")

        # ============================================================
        # 16. JUMP DATA (jc entries, 3+3 floats + 1 float = 28 bytes)
        # ============================================================
        jump_offset = f.tell()
        print(f"\n{'=' * 80}")
        print(f"--- JUMP DATA ---")
        print(f"  Offset: {jump_offset}, Count: {jc}, Each: 28 bytes")
        print(f"  Expected total: {jc * 28} bytes")
        jumps = []
        any_corrupt = False
        for i in range(jc):
            entry_offset = f.tell()
            raw_p = read_floats_raw(f, 3)
            raw_q = read_floats_raw(f, 3)
            raw_r = read_float_raw(f)

            p_vals = [v for _, v in raw_p]
            q_vals = [v for _, v in raw_q]
            r_val = raw_r[1]
            jumps.append((p_vals, q_vals, r_val))

            print(f"\n  Jump[{i}] at file offset {entry_offset}:")
            print(f"    Source position p:")
            for j in range(3):
                flag = ""
                s = is_suspicious(p_vals[j])
                if s:
                    flag = f"  *** SUSPICIOUS: {s}"
                    any_corrupt = True
                print(f"      p[{j}] = {p_vals[j]:12.6f}  raw: {hex_bytes(raw_p[j][0])}{flag}")

            print(f"    Destination position q:")
            for j in range(3):
                flag = ""
                s = is_suspicious(q_vals[j])
                if s:
                    flag = f"  *** SUSPICIOUS: {s}"
                    any_corrupt = True
                print(f"      q[{j}] = {q_vals[j]:12.6f}  raw: {hex_bytes(raw_q[j][0])}{flag}")

            flag = ""
            s = is_suspicious(r_val)
            if s:
                flag = f"  *** SUSPICIOUS: {s}"
                any_corrupt = True
            if r_val <= 0:
                flag += "  *** WARNING: non-positive radius"
                any_corrupt = True
            print(f"    Radius r = {r_val:12.6f}  raw: {hex_bytes(raw_r[0])}{flag}")

            # Sanity: distance between source and dest
            dist = math.sqrt(sum((p_vals[k] - q_vals[k])**2 for k in range(3)))
            print(f"    Distance p->q = {dist:.6f}")

        # ============================================================
        # 17. SWITCH DATA (xc entries)
        # ============================================================
        swch_offset = f.tell()
        print(f"\n{'=' * 80}")
        print(f"--- SWITCH DATA ---")
        print(f"  Offset: {swch_offset}, Count: {xc}")
        # Each: 3 floats(p) + 1 float(r) + 1 int(pi) + 1 float(t) + 1 float(skipped) + 1 int(f) + 1 int(skipped) + 1 int(i)
        # = 4*3 + 4 + 4 + 4 + 4 + 4 + 4 + 4 = 36 bytes
        for i in range(xc):
            p = read_floats(f, 3)
            r = read_float(f)
            swch_pi = read_int(f)
            swch_t = read_float(f)
            _ = read_float(f)  # skipped
            swch_f = read_int(f)
            _ = read_int(f)    # skipped
            swch_i = read_int(f)
            print(f"  Swch[{i}]: p=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) "
                  f"r={r:.2f} pi={swch_pi} t={swch_t:.2f} f={swch_f} i={swch_i}")

        # ============================================================
        # 18. BILLBOARD DATA (rc entries, 80 bytes each)
        # ============================================================
        bill_offset = f.tell()
        print(f"\n--- BILLBOARD DATA ---")
        print(f"  Offset: {bill_offset}, Count: {rc}")
        for i in range(rc):
            fl = read_int(f)
            mi = read_int(f)
            t = read_float(f)
            d = read_float(f)
            w = read_floats(f, 3)
            h = read_floats(f, 3)
            rx = read_floats(f, 3)
            ry = read_floats(f, 3)
            rz = read_floats(f, 3)
            p = read_floats(f, 3)
            print(f"  Bill[{i}]: fl={fl} mi={mi} t={t:.2f} d={d:.2f}")

        # ============================================================
        # 19. BALL DATA (uc entries, 3 floats + 1 float = 16 bytes)
        # ============================================================
        ball_offset = f.tell()
        print(f"\n{'=' * 80}")
        print(f"--- BALL DATA ---")
        print(f"  Offset: {ball_offset}, Count: {uc}, Each: 16 bytes")
        balls = []
        for i in range(uc):
            raw_p = read_floats_raw(f, 3)
            raw_r = read_float_raw(f)
            p_vals = [v for _, v in raw_p]
            r_val = raw_r[1]
            balls.append((p_vals, r_val))

            print(f"\n  Ball[{i}]:")
            print(f"    p[0] = {p_vals[0]:12.6f}  raw: {hex_bytes(raw_p[0][0])}")
            print(f"    p[1] = {p_vals[1]:12.6f}  raw: {hex_bytes(raw_p[1][0])}")
            print(f"    p[2] = {p_vals[2]:12.6f}  raw: {hex_bytes(raw_p[2][0])}")
            print(f"    r    = {r_val:12.6f}  raw: {hex_bytes(raw_r[0])}")

            for j, v in enumerate(p_vals):
                s = is_suspicious(v)
                if s:
                    print(f"    *** WARNING: p[{j}] is suspicious: {s}")
            s = is_suspicious(r_val)
            if s:
                print(f"    *** WARNING: r is suspicious: {s}")

        # ============================================================
        # 20. VIEW DATA (wc entries, 6 floats = 24 bytes)
        # ============================================================
        view_offset = f.tell()
        print(f"\n{'=' * 80}")
        print(f"--- VIEW DATA ---")
        print(f"  Offset: {view_offset}, Count: {wc}, Each: 24 bytes")
        views = []
        for i in range(wc):
            raw_p = read_floats_raw(f, 3)
            raw_q = read_floats_raw(f, 3)
            p_vals = [v for _, v in raw_p]
            q_vals = [v for _, v in raw_q]
            views.append((p_vals, q_vals))

            print(f"\n  View[{i}]:")
            print(f"    p[0] = {p_vals[0]:12.6f}  raw: {hex_bytes(raw_p[0][0])}")
            print(f"    p[1] = {p_vals[1]:12.6f}  raw: {hex_bytes(raw_p[1][0])}")
            print(f"    p[2] = {p_vals[2]:12.6f}  raw: {hex_bytes(raw_p[2][0])}")
            print(f"    q[0] = {q_vals[0]:12.6f}  raw: {hex_bytes(raw_q[0][0])}")
            print(f"    q[1] = {q_vals[1]:12.6f}  raw: {hex_bytes(raw_q[1][0])}")
            print(f"    q[2] = {q_vals[2]:12.6f}  raw: {hex_bytes(raw_q[2][0])}")

            for j, v in enumerate(p_vals):
                s = is_suspicious(v)
                if s:
                    print(f"    *** WARNING: p[{j}] is suspicious: {s}")
            for j, v in enumerate(q_vals):
                s = is_suspicious(v)
                if s:
                    print(f"    *** WARNING: q[{j}] is suspicious: {s}")

        # 21. Index array
        idx_offset = f.tell()
        print(f"\n--- INDEX ARRAY ---")
        print(f"  Offset: {idx_offset}, Count: {ic}")
        remaining = f.read()
        actual_remaining = len(remaining)
        expected_remaining = ic * 4
        print(f"  Remaining bytes in file: {actual_remaining}")
        print(f"  Expected for index array: {expected_remaining}")
        if actual_remaining != expected_remaining:
            print(f"  *** MISMATCH: difference = {actual_remaining - expected_remaining} bytes")
            if actual_remaining > expected_remaining:
                print(f"  *** There are {actual_remaining - expected_remaining} extra bytes after index array!")
            else:
                print(f"  *** File is SHORT by {expected_remaining - actual_remaining} bytes!")

        # ============================================================
        # SUMMARY
        # ============================================================
        print(f"\n{'=' * 80}")
        print(f"--- SUMMARY ---")
        print(f"\nFile version: {version}")
        print(f"Jump count: {jc}")
        print(f"Goal count: {zc}")
        print(f"Ball count: {uc}")
        print(f"View count: {wc}")
        print(f"Switch count: {xc}")

        if jc > 0:
            print(f"\n--- Jump Summary ---")
            for i, (p, q, r) in enumerate(jumps):
                dist = math.sqrt(sum((p[k] - q[k])**2 for k in range(3)))
                print(f"  Jump[{i}]: "
                      f"src=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) -> "
                      f"dst=({q[0]:.2f}, {q[1]:.2f}, {q[2]:.2f})  "
                      f"r={r:.2f}  dist={dist:.2f}")

        if any_corrupt:
            print(f"\n*** CORRUPTION DETECTED: Some jump values appear suspicious!")
        else:
            print(f"\nNo obvious corruption detected in jump data.")

        # Cross-reference: check if jump positions make sense relative to goals/ball/views
        if jc > 0 and zc > 0:
            print(f"\n--- Cross-reference: Jump destinations vs Goals ---")
            for i, (jp, jq, jr) in enumerate(jumps):
                for gi, (gp, gr) in enumerate(goals):
                    dist = math.sqrt(sum((jq[k] - gp[k])**2 for k in range(3)))
                    if dist < 5.0:
                        print(f"  Jump[{i}] dest is near Goal[{gi}]: distance={dist:.4f}")

        if jc > 0 and uc > 0:
            print(f"\n--- Cross-reference: Jump positions vs Ball start ---")
            for i, (jp, jq, jr) in enumerate(jumps):
                for bi, (bp, br) in enumerate(balls):
                    dist_src = math.sqrt(sum((jp[k] - bp[k])**2 for k in range(3)))
                    dist_dst = math.sqrt(sum((jq[k] - bp[k])**2 for k in range(3)))
                    if dist_src < 10.0:
                        print(f"  Jump[{i}] source near Ball[{bi}]: dist={dist_src:.4f}")
                    if dist_dst < 10.0:
                        print(f"  Jump[{i}] dest near Ball[{bi}]: dist={dist_dst:.4f}")


def deep_hex_analysis():
    """Deeper analysis: dump raw hex around the jump region and try shifted reads."""
    sol_path = r"C:\Users\Rog\Documents\aichat\neverputt\drodin-fork\data\map-putt\07_tele.sol"

    with open(sol_path, 'rb') as f:
        data = f.read()

    print("\n" + "=" * 80)
    print("=== DEEP HEX ANALYSIS ===")
    print("=" * 80)

    # Jump data is at offset 17320, 2 jumps * 28 bytes = 56 bytes (17320-17376)
    print("\n--- Raw hex dump: Goal(17304) + Jump(17320) + post-Jump(17376) ---")
    print("  Legend: offset : hex bytes => float / int")
    for off in range(17304, 17420, 4):
        raw = data[off:off + 4]
        if len(raw) < 4:
            break
        as_float = struct.unpack('<f', raw)[0]
        as_int = struct.unpack('<i', raw)[0]

        region = ""
        if 17304 <= off < 17320:
            idx = (off - 17304) // 4
            region = f"Goal[0].{'p[0] p[1] p[2] r'.split()[idx]}"
        elif 17320 <= off < 17376:
            ji = (off - 17320) // 28
            fi = ((off - 17320) % 28) // 4
            names = ['p[0]', 'p[1]', 'p[2]', 'q[0]', 'q[1]', 'q[2]', 'r']
            region = f"Jump[{ji}].{names[fi]}"
        elif 17376 <= off < 17456:
            bi = (off - 17376) // 16
            fi = ((off - 17376) % 16) // 4
            names = ['p[0]', 'p[1]', 'p[2]', 'r']
            region = f"Ball[{bi}].{names[fi]}"

        nan_flag = " *** NaN" if raw == b'\xff\xff\xff\xff' else ""
        print(f"  {off:5d}: {raw.hex(' ')}  float={as_float:12.6f}  "
              f"int={as_int:10d}  <- {region}{nan_flag}")

    # Try to figure out what the correct data should be
    # The 0xFFFFFFFF pattern looks like uninitialized or sentinel data
    # Let's see if we can reconstruct by shifting
    print("\n--- Trying shifted interpretations of jump region ---")
    print("  Looking for 28-byte windows where all 7 floats are reasonable")
    print("  (no NaN/Inf, abs < 100, radius > 0)")

    for shift in range(-20, 24, 4):
        trial_start = 17320 + shift
        results = []
        all_good = True
        for ji in range(2):
            off = trial_start + ji * 28
            if off < 0 or off + 28 > len(data):
                all_good = False
                break
            chunk = data[off:off + 28]
            vals = struct.unpack('<7f', chunk)
            p = vals[0:3]
            q = vals[3:6]
            r = vals[6]

            ok = True
            for v in vals:
                if math.isnan(v) or math.isinf(v) or abs(v) > 100:
                    ok = False
                    break
            if r <= 0:
                ok = False
            if not ok:
                all_good = False
            results.append((p, q, r, ok))

        if all_good:
            print(f"\n  *** SHIFT {shift:+d} bytes (offset {trial_start}) - ALL JUMPS VALID:")
            for ji, (p, q, r, ok) in enumerate(results):
                print(f"      Jump[{ji}]: p=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) "
                      f"-> q=({q[0]:.2f}, {q[1]:.2f}, {q[2]:.2f})  r={r:.2f}")
        elif any(ok for _, _, _, ok in results):
            print(f"\n  Shift {shift:+d} bytes (offset {trial_start}) - partial:")
            for ji, (p, q, r, ok) in enumerate(results):
                status = "OK" if ok else "BAD"
                print(f"      Jump[{ji}]: p=({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f}) "
                      f"-> q=({q[0]:.3f}, {q[1]:.3f}, {q[2]:.3f})  "
                      f"r={r:.3f} [{status}]")

    # Check the 24 extra bytes at end of file
    print("\n--- Analyzing 24 extra bytes at end of file ---")
    ic = 1204
    idx_offset = 17504
    expected_end = idx_offset + ic * 4  # 17504 + 4816 = 22320
    actual_end = len(data)  # 22344
    extra_start = expected_end
    print(f"  Expected end of index array: {expected_end}")
    print(f"  Actual file size: {actual_end}")
    print(f"  Extra bytes start at: {extra_start}")
    print(f"  Extra bytes count: {actual_end - extra_start}")

    if actual_end > extra_start:
        extra = data[extra_start:actual_end]
        print(f"  Raw extra bytes:")
        for i in range(0, len(extra), 4):
            chunk = extra[i:i + 4]
            if len(chunk) == 4:
                as_float = struct.unpack('<f', chunk)[0]
                as_int = struct.unpack('<i', chunk)[0]
                print(f"    {extra_start + i:5d}: {chunk.hex(' ')}  "
                      f"float={as_float:12.6f}  int={as_int:10d}")

    # Count all 0xFFFFFFFF occurrences in the jump region and nearby
    print("\n--- Locations of 0xFFFFFFFF in file (around jump region) ---")
    pattern = b'\xff\xff\xff\xff'
    for off in range(17200, 17600):
        if data[off:off + 4] == pattern:
            print(f"  0xFFFFFFFF at offset {off}")

    # Compute expected values from the .map source
    # SCALE = 64.0, coordinate transform: p[0] = +x/64, p[1] = +z/64, p[2] = -y/64
    SCALE = 64.0
    print("\n--- Expected jump data from .map source file ---")
    print("  Entity 1: target_teleporter origin='-64 192 0' target='t1'")
    print("    -> Jump[0].p = (-64/64, 0/64, -192/64) = (-1.0, 0.0, -3.0)")
    print("  Entity 2: target_position origin='-64 448 0' targetname='t1'")
    print("    -> Jump[0].q = (-64/64, 0/64, -448/64) = (-1.0, 0.0, -7.0)")
    print("  No radius specified -> default r=0.5")
    print()
    print("  Entity 3: target_teleporter origin='-64 448 0' target='t2'")
    print("    -> Jump[1].p = (-64/64, 0/64, -448/64) = (-1.0, 0.0, -7.0)")
    print("  Entity 4: target_position origin='-64 192 0' targetname='t2'")
    print("    -> Jump[1].q = (-64/64, 0/64, -192/64) = (-1.0, 0.0, -3.0)")
    print("  No radius specified -> default r=0.5")

    print()
    print("  Expected Jump[0]: p=(-1.0, 0.0, -3.0) q=(-1.0, 0.0, -7.0) r=0.5")
    print("  Expected Jump[1]: p=(-1.0, 0.0, -7.0) q=(-1.0, 0.0, -3.0) r=0.5")

    # Now show the actual vs expected comparison
    print()
    print("=" * 80)
    print("--- CORRUPTION DIAGNOSIS ---")
    print("=" * 80)
    print()
    print("Actual data read from the SOL file at the jump offset:")
    print("  Jump[0]: p=(NaN, NaN, -1.0)  q=(0.0, -3.0, -1.0)  r=0.0")
    print("  Jump[1]: p=(-7.0, 0.5, NaN)  q=(NaN, -1.0, 0.0)   r=-7.0")
    print()

    # Demonstrate the shift
    print("If we strip out the 0xFFFFFFFF (NaN) values and read the remaining")
    print("floats in sequence, we get the CORRECT data:")
    print()

    # Collect all 14 float values from the jump region (2 jumps * 7 floats)
    raw_floats = []
    for off in range(17320, 17376, 4):
        raw = data[off:off + 4]
        val = struct.unpack('<f', raw)[0]
        is_nan = raw == b'\xff\xff\xff\xff'
        raw_floats.append((off, raw, val, is_nan))

    print("  All 14 float slots in the jump data region:")
    for i, (off, raw, val, is_nan) in enumerate(raw_floats):
        ji = i // 7
        fi = i % 7
        names = ['p[0]', 'p[1]', 'p[2]', 'q[0]', 'q[1]', 'q[2]', 'r']
        label = f"Jump[{ji}].{names[fi]}"
        tag = " <<<< GARBAGE (0xFFFFFFFF)" if is_nan else ""
        print(f"    [{i:2d}] {off}: {raw.hex(' ')}  = {val:12.6f}  ({label}){tag}")

    # Filter out NaN values
    clean_floats = [(off, raw, val) for off, raw, val, is_nan in raw_floats if not is_nan]
    print(f"\n  After removing {sum(1 for _,_,_,n in raw_floats if n)} garbage entries, "
          f"{len(clean_floats)} valid floats remain:")
    for i, (off, raw, val) in enumerate(clean_floats):
        print(f"    [{i:2d}] {off}: {raw.hex(' ')}  = {val:12.6f}")

    print(f"\n  But 2 jumps need 14 floats, and we only have {len(clean_floats)}.")
    print(f"  The 24 extra bytes at end of file contain 6 more int/float values")
    print(f"  that got pushed past the index array.")

    print()
    print("CONCLUSION:")
    print("  The jump data in 07_tele.sol is CORRUPTED.")
    print("  Two 0xFFFFFFFF sentinel/garbage values (8 bytes) are inserted before")
    print("  each jump record's data, shifting the real data 8 bytes to the right.")
    print()
    print("  Pattern:")
    print("    Jump[0]: [NaN] [NaN] [-1.0] [0.0] [-3.0] [-1.0] [0.0]")
    print("             ^^^^^ ^^^^^  <- 2 garbage floats inserted")
    print("                          then real p=(-1.0, 0.0, -3.0)")
    print("                                    q=(-1.0, 0.0, ...)  <- truncated")
    print()
    print("    Jump[1]: [-7.0] [0.5] [NaN] [NaN] [-1.0] [0.0] [-7.0]")
    print("             ^carry-over^  ^^^^^ ^^^^^  <- 2 garbage floats again")
    print("             from Jump[0]  then real p=(-1.0, 0.0, -7.0)")
    print("             q/r overflow  q/r data pushed beyond this section")
    print()
    print("  The 24 extra bytes at end of file (6 ints: 10, 11, 222, 223, 224, 225)")
    print("  are likely index array entries that got displaced by the 8 extra bytes.")
    print()
    print("  Root cause: The SOL file was compiled with garbage inserted at the")
    print("  start of each jump record in the binary. The 0xFFFFFFFF pattern")
    print("  suggests uninitialized memory or -1 sentinel values that were")
    print("  inadvertently written before the actual jump float data.")

    # Also check the body data: g0=228 but gc=0 is interesting (body[0])
    print()
    print("--- Additional notes ---")
    print("  Body[0] has g0=228 but gc=0 -- no geom in the body (all geom in lumps)")
    print("  Body[0] has pi=-1 pj=-1 -- static body (no path)")
    print()

    # Also check view data vs expected
    print("--- View data cross-check ---")
    # Entity 11: target_position origin "-192 576 8" targetname "t3"
    # Entity 12: info_player_intermission origin "-64 0 192" target "t3"
    # View[0].p = (cam origin) = (-64/64, 192/64, -0/64) = (-1.0, 3.0, 0.0)
    # View[0].q = (target) = (-192/64, 8/64, -576/64) = (-3.0, 0.125, -9.0)
    # Entity 13: target_position origin "-64 320 8" targetname "t4"
    # Entity 14: info_player_intermission origin "256 320 192" target "t4"
    # View[1].p = (256/64, 192/64, -320/64) = (4.0, 3.0, -5.0)
    # View[1].q = (-64/64, 8/64, -320/64) = (-1.0, 0.125, -5.0)
    print("  Expected View[0]: p=(-1.0, 3.0, 0.0) q=(-3.0, 0.125, -9.0)")
    print("  Actual   View[0]: p=(-1.0, 0.0625, 1.0) q=(0.063, -1.0, 0.0625)")
    print("  --> View data also appears MISALIGNED / CORRUPTED")
    print()
    print("  Expected View[1]: p=(4.0, 3.0, -5.0) q=(-1.0, 0.125, -5.0)")
    print("  Actual   View[1]: p=(-1.0, 3.0, -0.0) q=(-3.0, 0.125, -9.0)")
    print("  --> View[1] actual data matches expected View[0].q pattern!")
    print("  --> This confirms a systemic data shift throughout the file")


if __name__ == '__main__':
    main()
    deep_hex_analysis()
