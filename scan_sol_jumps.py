#!/usr/bin/env python3
"""
Scan all .sol files under data/ and report which ones have jump count (jc) > 0,
and whether their jump data contains NaN values (0xFFFFFFFF bytes).

The SOL binary format is parsed based on solid_base.c from the neverball source.
"""

import os
import struct
import math
import glob

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SOL_MAGIC = 0xAF | (ord('S') << 8) | (ord('O') << 16) | (ord('L') << 24)

# Version constants
SOL_VERSION_1_5 = 6
SOL_VERSION_1_6 = 7
SOL_VERSION_DEV = 8
SOL_VERSION_1_7 = 9

PATHMAX = 64

# M_ALPHA_TEST = (1 << 9) = 512
M_ALPHA_TEST = 512

# P_ORIENTED = 1
P_ORIENTED = 1


class SOLReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read_int(self):
        val = struct.unpack_from('<i', self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_uint(self):
        val = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_float(self):
        val = struct.unpack_from('<f', self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_raw_uint(self):
        """Read 4 bytes as unsigned int (for NaN detection)."""
        val = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_bytes(self, n):
        val = self.data[self.pos:self.pos + n]
        self.pos += n
        return val

    def skip(self, n):
        self.pos += n

    def remaining(self):
        return len(self.data) - self.pos


def parse_sol_file(filepath):
    """Parse a SOL file and extract jump data. Returns a dict with results."""
    with open(filepath, 'rb') as f:
        data = f.read()

    file_size = len(data)
    result = {
        'file': filepath,
        'size': file_size,
        'error': None,
        'version': None,
        'jc': 0,
        'jumps': [],
        'has_nan': False,
        'nan_details': [],
    }

    if file_size < 8:
        result['error'] = "File too small"
        return result

    r = SOLReader(data)

    # Read magic and version
    magic = r.read_uint()
    if magic != SOL_MAGIC:
        result['error'] = f"Bad magic: 0x{magic:08X} (expected 0x{SOL_MAGIC:08X})"
        return result

    version = r.read_int()
    result['version'] = version

    if version < SOL_VERSION_1_5 or version > SOL_VERSION_1_7:
        result['error'] = f"Unsupported version: {version}"
        return result

    # Read index counts (sol_load_indx)
    ac = r.read_int()
    dc = r.read_int()
    mc = r.read_int()
    vc = r.read_int()
    ec = r.read_int()
    sc = r.read_int()
    tc = r.read_int()

    if version >= SOL_VERSION_1_6:
        oc = r.read_int()
    else:
        oc = 0

    gc = r.read_int()
    lc = r.read_int()
    nc = r.read_int()
    pc = r.read_int()
    bc = r.read_int()
    hc = r.read_int()
    zc = r.read_int()
    jc = r.read_int()
    xc = r.read_int()
    rc = r.read_int()
    uc = r.read_int()
    wc = r.read_int()
    ic = r.read_int()

    result['jc'] = jc
    result['counts'] = {
        'ac': ac, 'dc': dc, 'mc': mc, 'vc': vc, 'ec': ec,
        'sc': sc, 'tc': tc, 'oc': oc, 'gc': gc, 'lc': lc,
        'nc': nc, 'pc': pc, 'bc': bc, 'hc': hc, 'zc': zc,
        'jc': jc, 'xc': xc, 'rc': rc, 'uc': uc, 'wc': wc, 'ic': ic,
    }

    if jc == 0:
        return result

    # Now we need to skip through all preceding data sections to reach jumps.
    # Data order: av, dv, mv, vv, ev, sv, tv, ov, gv, lv, nv, pv, bv, hv, zv, jv

    # av: ac bytes (chars)
    r.skip(ac)

    # dv: dc * 2 ints = dc * 8 bytes (ai, aj)
    r.skip(dc * 8)

    # mv: mc materials - variable size!
    # Each material: d[4] + a[4] + s[4] + e[4] + h[1] = 17 floats + 1 int (fl) + 64 bytes (filename)
    # Base: 17*4 + 4 + 64 = 68 + 4 + 64 = 136 bytes
    # If version >= 1.6 and fl & M_ALPHA_TEST: +4 (alpha_func int) +4 (alpha_ref float) = +8
    for i in range(mc):
        # d[4], a[4], s[4], e[4], h[1] = 17 floats
        r.skip(17 * 4)
        # fl = int
        fl = r.read_int()
        # f[PATHMAX] = 64 bytes
        r.skip(PATHMAX)
        # conditional alpha test fields
        if version >= SOL_VERSION_1_6:
            if fl & M_ALPHA_TEST:
                r.skip(4 + 4)  # alpha_func + alpha_ref

    # vv: vc * 3 floats = vc * 12 bytes
    r.skip(vc * 12)

    # ev: ec * 2 ints = ec * 8 bytes
    r.skip(ec * 8)

    # sv: sc * (3 floats + 1 float) = sc * 16 bytes
    r.skip(sc * 16)

    # tv: tc * 2 floats = tc * 8 bytes
    r.skip(tc * 8)

    # ov: oc * 3 ints = oc * 12 bytes
    if version >= SOL_VERSION_1_6:
        r.skip(oc * 12)

    # gv: gc * geoms - variable depending on version
    if version >= SOL_VERSION_1_6:
        # mi, oi, oj, ok = 4 ints per geom
        r.skip(gc * 16)
    else:
        # mi + 3 * (ti, si, vi) = 1 + 9 = 10 ints per geom
        r.skip(gc * 40)

    # lv: lc * 9 ints (fl, v0, vc, e0, ec, g0, gc, s0, sc) = lc * 36
    r.skip(lc * 36)

    # nv: nc * 5 ints (si, ni, nj, l0, lc) = nc * 20
    r.skip(nc * 20)

    # pv: pc paths - variable size!
    # Each path: p[3] floats + t float + pi int + f int + s int = 3+1=4 floats + 3 ints = 28 bytes base
    # if version >= 1.6: + fl int = 32 bytes
    # if fl & P_ORIENTED: + e[4] floats = +16 bytes
    # version 1.5: p[3] + t + pi + f + s = 7 * 4 = 28 bytes, no fl, no orient
    for i in range(pc):
        r.skip(3 * 4)   # p[3]
        r.skip(4)        # t (float)
        r.skip(4)        # pi (int)
        r.skip(4)        # f (int)
        r.skip(4)        # s (int)

        if version >= SOL_VERSION_1_6:
            fl = r.read_int()  # fl
            if fl & P_ORIENTED:
                r.skip(4 * 4)  # e[4]
        else:
            fl = 0

    # bv: bc bodies - variable depending on version
    if version >= SOL_VERSION_1_6:
        # pi, pj, ni, l0, lc, g0, gc = 7 ints = 28 bytes
        r.skip(bc * 28)
    else:
        # pi, ni, l0, lc, g0, gc = 6 ints = 24 bytes (no pj in v1.5)
        # Actually looking at the code more carefully:
        # version >= 1.6: pi + pj + ni + l0 + lc + g0 + gc = 7 ints
        # version < 1.6: pi + ni + l0 + lc + g0 + gc = 6 ints
        r.skip(bc * 24)

    # hv: hc * (p[3] floats + t int + n int) = hc * 20 bytes
    r.skip(hc * 20)

    # zv: zc * (p[3] floats + r float) = zc * 16 bytes
    r.skip(zc * 16)

    # NOW we are at the jump data!
    jump_start_offset = r.pos
    result['jump_offset'] = jump_start_offset

    # Each jump: p[3] + q[3] + r = 7 floats = 28 bytes
    for i in range(jc):
        jump_offset = r.pos
        # Read 7 floats as both float and raw uint32
        raw_values = []
        float_values = []
        for j in range(7):
            raw = struct.unpack_from('<I', data, r.pos)[0]
            fval = struct.unpack_from('<f', data, r.pos)[0]
            raw_values.append(raw)
            float_values.append(fval)
            r.pos += 4

        p = float_values[0:3]
        q = float_values[3:6]
        radius = float_values[6]

        nan_fields = []
        field_names = ['p[0]', 'p[1]', 'p[2]', 'q[0]', 'q[1]', 'q[2]', 'r']
        for j in range(7):
            if raw_values[j] == 0xFFFFFFFF:
                nan_fields.append(f"{field_names[j]}=0xFFFFFFFF (NaN)")
            elif math.isnan(float_values[j]):
                nan_fields.append(f"{field_names[j]}=0x{raw_values[j]:08X} (NaN)")
            elif math.isinf(float_values[j]):
                nan_fields.append(f"{field_names[j]}=0x{raw_values[j]:08X} (Inf)")

        jump_info = {
            'index': i,
            'offset': jump_offset,
            'p': p,
            'q': q,
            'r': radius,
            'raw': raw_values,
            'nan_fields': nan_fields,
        }
        result['jumps'].append(jump_info)

        if nan_fields:
            result['has_nan'] = True
            result['nan_details'].extend(nan_fields)

    return result


def main():
    sol_files = glob.glob(os.path.join(DATA_DIR, "**", "*.sol"), recursive=True)
    sol_files.sort()

    print(f"Scanning {len(sol_files)} .sol files under {DATA_DIR}")
    print("=" * 80)

    files_with_jumps = []
    files_with_nan = []
    total_jumps = 0
    errors = []

    for filepath in sol_files:
        try:
            result = parse_sol_file(filepath)
        except Exception as e:
            rel = os.path.relpath(filepath, DATA_DIR)
            errors.append((rel, str(e)))
            continue

        if result['error']:
            rel = os.path.relpath(filepath, DATA_DIR)
            errors.append((rel, result['error']))
            continue

        if result['jc'] > 0:
            files_with_jumps.append(result)
            total_jumps += result['jc']
            if result['has_nan']:
                files_with_nan.append(result)

    # Report files with jumps
    print(f"\nFiles with jc > 0: {len(files_with_jumps)}")
    print(f"Total jump entities across all files: {total_jumps}")
    print("-" * 80)

    for result in files_with_jumps:
        rel = os.path.relpath(result['file'], DATA_DIR)
        print(f"\n  {rel}")
        print(f"    Version: {result['version']}  |  Size: {result['size']} bytes  |  jc: {result['jc']}")
        if 'jump_offset' in result:
            print(f"    Jump data starts at offset: 0x{result['jump_offset']:X} ({result['jump_offset']})")

        for jump in result['jumps']:
            p = jump['p']
            q = jump['q']
            r = jump['r']
            raw = jump['raw']

            # Format position and target
            def fmt_float(val, raw_val):
                if raw_val == 0xFFFFFFFF:
                    return "NaN(0xFFFFFFFF)"
                elif math.isnan(val):
                    return f"NaN(0x{raw_val:08X})"
                elif math.isinf(val):
                    return f"Inf(0x{raw_val:08X})"
                else:
                    return f"{val:.4f}"

            p_str = f"({fmt_float(p[0], raw[0])}, {fmt_float(p[1], raw[1])}, {fmt_float(p[2], raw[2])})"
            q_str = f"({fmt_float(q[0], raw[3])}, {fmt_float(q[1], raw[4])}, {fmt_float(q[2], raw[5])})"
            r_str = fmt_float(r, raw[6])

            nan_marker = " *** HAS NaN ***" if jump['nan_fields'] else ""
            print(f"    Jump[{jump['index']}] @ 0x{jump['offset']:X}: p={p_str} q={q_str} r={r_str}{nan_marker}")

            if jump['nan_fields']:
                for nf in jump['nan_fields']:
                    print(f"      >> {nf}")

    # Summary of NaN findings
    print("\n" + "=" * 80)
    print(f"\nFiles with NaN values in jump data: {len(files_with_nan)}")
    if files_with_nan:
        for result in files_with_nan:
            rel = os.path.relpath(result['file'], DATA_DIR)
            print(f"  ** {rel} (jc={result['jc']})")
            for detail in result['nan_details']:
                print(f"       {detail}")
    else:
        print("  (none - all jump data appears valid)")

    # Report errors
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for rel, err in errors:
            print(f"  {rel}: {err}")

    print("\nDone.")


if __name__ == '__main__':
    main()
