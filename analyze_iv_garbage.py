#!/usr/bin/env python3
"""Analyze garbage prefix in iv[] array of SOL files."""

import struct
import sys
import os
import glob
from collections import Counter

SOL_VERSION_1_6 = 7
M_ALPHA_TEST = 1 << 9
P_ORIENTED = 1
PATHMAX = 64


def read_int(f):
    data = f.read(4)
    if len(data) < 4:
        raise EOFError("Unexpected EOF at offset %d" % f.tell())
    return struct.unpack("<i", data)[0]


def read_raw4(f):
    data = f.read(4)
    if len(data) < 4:
        raise EOFError("Unexpected EOF at offset %d" % f.tell())
    return data


def analyze_sol(filepath):
    result = {"filename": os.path.basename(filepath), "error": None}
    try:
        with open(filepath, "rb") as f:
            file_size = f.seek(0, 2)
            f.seek(0)
            magic = read_int(f)
            version = read_int(f)
            expected_magic = 0xAF | (ord("S") << 8) | (ord("O") << 16) | (ord("L") << 24)
            if magic != expected_magic:
                result["error"] = "Bad magic"
                return result
            result["version"] = version
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
            f.read(ac)
            f.read(dc * 8)
            for i in range(mc):
                f.read(64)
                f.read(4)
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
            if version >= SOL_VERSION_1_6:
                f.read(gc * 16)
            else:
                f.read(gc * 40)
            f.read(lc * 36)
            f.read(nc * 20)
            for i in range(pc):
                f.read(28)
                fl = 0
                if version >= SOL_VERSION_1_6:
                    fl = read_int(f)
                if fl & P_ORIENTED:
                    f.read(16)
            if version >= SOL_VERSION_1_6:
                f.read(bc * 28)
            else:
                f.read(bc * 24)
            f.read(hc * 20)
            f.read(zc * 16)
            f.read(jc * 28)
            f.read(xc * 40)
            f.read(rc * 88)
            f.read(uc * 16)
            f.read(wc * 24)
            iv_start_offset = f.tell()
            result["iv_start_offset"] = iv_start_offset
            iv = []
            iv_raw = []
            for i in range(ic):
                raw = read_raw4(f)
                iv_raw.append(raw)
                iv.append(struct.unpack("<i", raw)[0])
            trailing_data = f.read()
            trailing_bytes = len(trailing_data)
            trailing_ints = []
            for i in range(0, trailing_bytes - (trailing_bytes % 4), 4):
                trailing_ints.append(struct.unpack("<i", trailing_data[i:i + 4])[0])
            result["ic"] = ic
            result["trailing_bytes"] = trailing_bytes
            result["trailing_ints"] = trailing_ints
            result["file_size"] = file_size
            max_valid = max(vc, ec, sc, gc) if (vc or ec or sc or gc) else 1
            result["max_valid"] = max_valid
            result["vc"] = vc
            result["ec"] = ec
            result["sc"] = sc
            result["gc"] = gc
            garbage_count = 0
            for i in range(ic):
                if iv[i] < 0 or iv[i] >= max_valid:
                    garbage_count += 1
                else:
                    break
            result["garbage_prefix_len"] = garbage_count
            garbage_details = []
            for i in range(min(garbage_count, 10)):
                val = iv[i]
                fval = struct.unpack("<f", iv_raw[i])[0]
                garbage_details.append({"index": i, "int_val": val,
                    "hex": "0x{:08X}".format(val & 0xFFFFFFFF), "float_val": fval})
            result["garbage_details"] = garbage_details
            trailing_details = []
            for i, val in enumerate(trailing_ints[:10]):
                trailing_details.append({"index": i, "int_val": val,
                    "valid": 0 <= val < max_valid})
            result["trailing_details"] = trailing_details
    except Exception as e:
        import traceback
        result["error"] = str(e) + "\n" + traceback.format_exc()
    return result


def main():
    sol_dir = r"C:\Users\Rog\Documents\aichat\neverputt\drodin-fork\android\app\src\main\assets\data\map-putt"
    sol_files = sorted(glob.glob(os.path.join(sol_dir, "*.sol")))
    if not sol_files:
        print("No .sol files found!")
        return
    print("Found %d .sol files" % len(sol_files))
    print()
    results = []
    for fp in sol_files:
        r = analyze_sol(fp)
        results.append(r)
    print("=" * 170)
    header = "%-20s %3s %6s %6s %6s %6s %6s %6s %5s %5s  %s" % (
        "Filename", "Ver", "ic", "vc", "ec", "sc", "gc", "max_v", "garb#", "trail",
        "First garbage values (hex -> float)")
    print(header)
    print("=" * 170)
    for r in sorted(results, key=lambda x: x["filename"]):
        if r.get("error"):
            first_line = str(r["error"]).split("\n")[0][:80]
            print("%-20s ERROR: %s" % (r["filename"], first_line))
            continue
        name = r["filename"]
        ver = r.get("version", 0)
        ic = r["ic"]
        vc_ = r["vc"]
        ec_ = r["ec"]
        sc_ = r["sc"]
        gc_ = r["gc"]
        max_v = r["max_valid"]
        garb = r["garbage_prefix_len"]
        trail = r["trailing_bytes"]
        garb_str = ""
        for g in r["garbage_details"]:
            garb_str += "  %s=%.6g" % (g["hex"], g["float_val"])
        print("%-20s %3d %6d %6d %6d %6d %6d %6d %5d %5d%s" % (
            name, ver, ic, vc_, ec_, sc_, gc_, max_v, garb, trail, garb_str))
    print()
    print()
    print("=" * 100)
    print("DETAILED ANALYSIS OF FILES WITH GARBAGE PREFIX")
    print("=" * 100)
    for r in sorted(results, key=lambda x: x["filename"]):
        if r.get("error") or r.get("garbage_prefix_len", 0) == 0:
            continue
        print()
        print("--- %s ---" % r["filename"])
        print("  iv[] starts at file offset: %d (0x%X)" % (r["iv_start_offset"], r["iv_start_offset"]))
        print("  ic=%d, max_valid=%d" % (r["ic"], r["max_valid"]))
        print("  Garbage prefix length: %d" % r["garbage_prefix_len"])
        print("  Trailing bytes after iv[]: %d" % r["trailing_bytes"])
        print("  Garbage entries:")
        for g in r["garbage_details"]:
            print("    iv[%d] = %12d  %s  as_float=%s" % (g["index"], g["int_val"], g["hex"], g["float_val"]))
        if r["trailing_details"]:
            print("  Trailing int values (after iv[ic-1]):")
            for t in r["trailing_details"]:
                vm = "VALID" if t["valid"] else "OUT_OF_RANGE"
                print("    extra[%d] = %6d  (%s)" % (t["index"], t["int_val"], vm))
        garb = r["garbage_prefix_len"]
        trail_ints = r["trailing_bytes"] // 4
        if garb == trail_ints:
            print("  ** MATCH: garbage_prefix(%d) == trailing_ints(%d) -- shift confirmed **" % (garb, trail_ints))
        elif trail_ints > 0:
            print("  ** MISMATCH: garbage_prefix(%d) != trailing_ints(%d) **" % (garb, trail_ints))
        else:
            print("  ** No trailing data -- garbage not recoverable from file **")
    print()
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    total = len(results)
    with_garbage = sum(1 for r in results if r.get("garbage_prefix_len", 0) > 0)
    no_garbage = sum(1 for r in results if r.get("garbage_prefix_len", 0) == 0 and not r.get("error"))
    errors = sum(1 for r in results if r.get("error"))
    print("  Total files:      %d" % total)
    print("  With garbage:     %d" % with_garbage)
    print("  Clean:            %d" % no_garbage)
    print("  Errors:           %d" % errors)
    garb_counts = Counter(r.get("garbage_prefix_len", -1) for r in results if not r.get("error"))
    print()
    print("  Garbage prefix length distribution:")
    for length, count in sorted(garb_counts.items()):
        print("    prefix_len=%d: %d files" % (length, count))


if __name__ == "__main__":
    main()
