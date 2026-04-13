#!/usr/bin/env python3
"""Dump detailed SOL structure for diagnosis."""

import struct
import sys
import os
import math

SOL_VERSION_1_6 = 7
M_ALPHA_TEST = 1 << 9
P_ORIENTED = 1
PATHMAX = 64

def read_int(f):
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(f"Unexpected EOF at offset {f.tell()}")
    return struct.unpack('<i', data)[0]

def read_float(f):
    data = f.read(4)
    if len(data) < 4:
        raise EOFError(f"Unexpected EOF at offset {f.tell()}")
    return struct.unpack('<f', data)[0]

def read_floats(f, n):
    data = f.read(4 * n)
    return struct.unpack(f'<{n}f', data)

def dump_sol(filepath):
    with open(filepath, 'rb') as f:
        magic = read_int(f)
        version = read_int(f)

        expected_magic = 0xAF | (ord('S') << 8) | (ord('O') << 16) | (ord('L') << 24)
        if magic != expected_magic:
            print("Not a valid SOL file!")
            return

        print(f"SOL version: {version}")

        # Read counts
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

        print(f"Counts: text={ac} dict={dc} mtrl={mc} vert={vc} edge={ec} side={sc} texc={tc}")
        print(f"  offs={oc} geom={gc} lump={lc} node={nc} path={pc} body={bc}")
        print(f"  item={hc} goal={zc} jump={jc} swch={xc} bill={rc} ball={uc} view={wc} idx={ic}")

        # Read materials
        materials = []
        for i in range(mc):
            d = read_floats(f, 4)
            a = read_floats(f, 4)
            s = read_floats(f, 4)
            e = read_floats(f, 4)
            h = read_float(f)
            fl = read_int(f)
            name_bytes = f.read(PATHMAX)
            name = name_bytes.split(b'\x00')[0].decode('latin-1')
            alpha_func = alpha_ref = None
            if version >= SOL_VERSION_1_6 and (fl & M_ALPHA_TEST):
                alpha_func = read_int(f)
                alpha_ref = read_float(f)
            materials.append({'name': name, 'fl': fl})

        print(f"\n=== Materials ({mc}) ===")
        for i, m in enumerate(materials):
            flags = []
            fl = m['fl']
            flag_names = [
                (1<<0, 'CLAMP_T'), (1<<1, 'CLAMP_S'), (1<<2, 'ADDITIVE'),
                (1<<3, 'TWO_SIDED'), (1<<4, 'ENVIRONMENT'), (1<<5, 'DECAL'),
                (1<<6, 'SHADOWED'), (1<<7, 'TRANSPARENT'), (1<<8, 'REFLECTIVE'),
                (1<<9, 'ALPHA_TEST'), (1<<10, 'PARTICLE'), (1<<11, 'LIT')
            ]
            for bit, name in flag_names:
                if fl & bit:
                    flags.append(name)
            print(f"  [{i}] {m['name']:30s} fl=0x{fl:04x} ({' | '.join(flags)})")

        # Skip vertices
        f.read(vc * 12)
        # Skip edges
        f.read(ec * 8)
        # Skip sides
        f.read(sc * 16)
        # Skip texcoords
        f.read(tc * 8)
        # Skip offsets
        if version >= SOL_VERSION_1_6:
            f.read(oc * 12)

        # Read geoms
        geoms = []
        for i in range(gc):
            mi = read_int(f)
            if version >= SOL_VERSION_1_6:
                oi = read_int(f)
                oj = read_int(f)
                ok = read_int(f)
            else:
                # Old format - skip for now
                f.read(36)
                oi = oj = ok = 0
            geoms.append({'mi': mi, 'oi': oi, 'oj': oj, 'ok': ok})

        # Count geoms per material
        geom_per_mtrl = {}
        for i, g in enumerate(geoms):
            mi = g['mi']
            if mi not in geom_per_mtrl:
                geom_per_mtrl[mi] = []
            geom_per_mtrl[mi].append(i)

        print(f"\n=== Geoms ({gc}) per material ===")
        for mi in sorted(geom_per_mtrl.keys()):
            glist = geom_per_mtrl[mi]
            mname = materials[mi]['name'] if mi < mc else '???'
            print(f"  material[{mi}] {mname}: {len(glist)} geoms (indices: {glist[:10]}{'...' if len(glist) > 10 else ''})")

        # Read lumps
        lumps = []
        for i in range(lc):
            fl = read_int(f)
            v0 = read_int(f); vc_ = read_int(f)
            e0 = read_int(f); ec_ = read_int(f)
            g0 = read_int(f); gc_ = read_int(f)
            s0 = read_int(f); sc_ = read_int(f)
            lumps.append({'fl': fl, 'v0': v0, 'vc': vc_, 'e0': e0, 'ec': ec_,
                          'g0': g0, 'gc': gc_, 's0': s0, 'sc': sc_})

        # Read nodes
        nodes = []
        for i in range(nc):
            si = read_int(f)
            ni = read_int(f)
            nj = read_int(f)
            l0 = read_int(f)
            lc_ = read_int(f)
            nodes.append({'si': si, 'ni': ni, 'nj': nj, 'l0': l0, 'lc': lc_})

        # Read paths
        paths = []
        for i in range(pc):
            p = read_floats(f, 3)
            t = read_float(f)
            pi = read_int(f)
            pf = read_int(f)
            ps = read_int(f)
            fl = 0
            if version >= SOL_VERSION_1_6:
                fl = read_int(f)
            orient = None
            if fl & P_ORIENTED:
                orient = read_floats(f, 4)
            paths.append({'p': p, 't': t, 'pi': pi, 'f': pf, 's': ps, 'fl': fl, 'orient': orient})

        # Read bodies
        bodies = []
        for i in range(bc):
            pi = read_int(f)
            pj = read_int(f) if version >= SOL_VERSION_1_6 else -1
            ni = read_int(f)
            l0 = read_int(f)
            lc_ = read_int(f)
            g0 = read_int(f)
            gc_ = read_int(f)
            bodies.append({'pi': pi, 'pj': pj, 'ni': ni, 'l0': l0, 'lc': lc_, 'g0': g0, 'gc': gc_})

        # Read items
        items = []
        for i in range(hc):
            p = read_floats(f, 3)
            t = read_int(f)
            n = read_int(f)
            items.append({'p': p, 't': t, 'n': n})

        # Read goals (with sentinel detection)
        goals = []
        for i in range(zc):
            pos = f.tell()
            v0 = read_int(f)
            v1 = read_int(f)
            sentinel = (v0 == -1 and v1 == -1)
            if not sentinel:
                f.seek(pos)
            p = read_floats(f, 3)
            r = read_float(f)
            goals.append({'p': p, 'r': r, 'sentinel': sentinel})

        # Read jumps (with sentinel detection)
        jumps = []
        for i in range(jc):
            pos = f.tell()
            v0 = read_int(f)
            v1 = read_int(f)
            sentinel = (v0 == -1 and v1 == -1)
            if not sentinel:
                f.seek(pos)
            p = read_floats(f, 3)
            q = read_floats(f, 3)
            r = read_float(f)
            jumps.append({'p': p, 'q': q, 'r': r, 'sentinel': sentinel})

        # Read switches (with sentinel detection)
        switches = []
        for i in range(xc):
            pos = f.tell()
            v0_raw = f.read(4)
            v1_raw = f.read(4)
            v0 = struct.unpack('<i', v0_raw)[0]
            v1 = struct.unpack('<i', v1_raw)[0]
            v0f = struct.unpack('<f', v0_raw)[0]
            v1f = struct.unpack('<f', v1_raw)[0]
            sentinel = (v0 == -1 and v1 == -1)
            if not sentinel:
                f.seek(pos)
            data_pos = f.tell()
            p = read_floats(f, 3)
            r = read_float(f)
            pi_sw = read_int(f)
            t = read_float(f)
            t_dup = read_float(f)
            sf = read_int(f)
            sf_dup = read_int(f)
            si = read_int(f)
            switches.append({
                'p': p, 'r': r, 'pi': pi_sw, 't': t, 't_dup': t_dup,
                'f': sf, 'f_dup': sf_dup, 'i': si,
                'sentinel': sentinel, 'sentinel_pos': pos, 'data_pos': data_pos,
                'peek_int': (v0, v1), 'peek_float': (v0f, v1f),
                'peek_hex': (v0_raw.hex(), v1_raw.hex())
            })

        # Skip billboards
        f.read(rc * 88)

        # Read balls
        balls = []
        for i in range(uc):
            p = read_floats(f, 3)
            r = read_float(f)
            balls.append({'p': p, 'r': r})

        # Read views
        views = []
        for i in range(wc):
            p = read_floats(f, 3)
            q = read_floats(f, 3)
            views.append({'p': p, 'q': q})
        idx_array = []
        for i in range(ic):
            idx_array.append(read_int(f))

        print(f"\n=== Paths ({pc}) ===")
        for i, p in enumerate(paths):
            print(f"  path[{i}]: p=({p['p'][0]:.4f}, {p['p'][1]:.4f}, {p['p'][2]:.4f}) t={p['t']:.4f} pi={p['pi']} f={p['f']} s={p['s']}")

        print(f"\n=== Bodies ({bc}) ===")
        for i, b in enumerate(bodies):
            print(f"  body[{i}]: pi={b['pi']} pj={b['pj']} ni={b['ni']} l0={b['l0']} lc={b['lc']} g0={b['g0']} gc={b['gc']}")

        print(f"\n=== Goals ({zc}) ===")
        for i, g in enumerate(goals):
            print(f"  goal[{i}]: p=({g['p'][0]:.4f}, {g['p'][1]:.4f}, {g['p'][2]:.4f}) r={g['r']:.4f} sentinel={g['sentinel']}")

        print(f"\n=== Switches ({xc}) ===")
        for i, s in enumerate(switches):
            print(f"  swch[{i}]: p=({s['p'][0]:.4f}, {s['p'][1]:.4f}, {s['p'][2]:.4f}) r={s['r']:.4f} pi={s['pi']} t={s['t']:.4f} f={s['f']} i={s['i']}")
            print(f"           sentinel={s['sentinel']} peek_int={s['peek_int']} peek_hex=({s['peek_hex'][0]}, {s['peek_hex'][1]})")
            print(f"           t_dup={s['t_dup']:.4f} f_dup={s['f_dup']} sentinel_pos={s['sentinel_pos']} data_pos={s['data_pos']}")

        print(f"\n=== Balls ({uc}) ===")
        for i, b in enumerate(balls):
            print(f"  ball[{i}]: p=({b['p'][0]:.4f}, {b['p'][1]:.4f}, {b['p'][2]:.4f}) r={b['r']:.4f}")

        print(f"\n=== Views ({wc}) ===")
        for i, v in enumerate(views):
            print(f"  view[{i}]: p=({v['p'][0]:.4f}, {v['p'][1]:.4f}, {v['p'][2]:.4f}) q=({v['q'][0]:.4f}, {v['q'][1]:.4f}, {v['q'][2]:.4f})")

        print(f"\n=== Lumps ({lc}) ===")
        for i, l in enumerate(lumps):
            print(f"  lump[{i}]: fl={l['fl']} g0={l['g0']} gc={l['gc']} v0={l['v0']} vc={l['vc']}")

        print(f"\n=== Index array ({ic} entries) ===")
        if ic <= 200:
            for i in range(0, ic, 20):
                chunk = idx_array[i:i+20]
                print(f"  [{i:4d}] {' '.join(f'{v:3d}' for v in chunk)}")
        else:
            print(f"  (too large to print all, first 100:)")
            for i in range(0, min(100, ic), 20):
                chunk = idx_array[i:i+20]
                print(f"  [{i:4d}] {' '.join(f'{v:3d}' for v in chunk)}")

        # Now trace: for each body, which materials are reachable?
        print(f"\n=== Material reachability from bodies ===")
        for bi, b in enumerate(bodies):
            print(f"\n  Body[{bi}]:")
            mtrl_geoms = {}

            # Trace through lumps
            for li in range(b['lc']):
                lump = lumps[b['l0'] + li]
                g0 = lump['g0']
                gc_ = lump['gc']
                for gi in range(gc_):
                    if g0 + gi < ic:
                        geom_idx = idx_array[g0 + gi]
                        if geom_idx < gc:
                            mi = geoms[geom_idx]['mi']
                            if mi not in mtrl_geoms:
                                mtrl_geoms[mi] = []
                            mtrl_geoms[mi].append((li, geom_idx))
                        else:
                            print(f"    WARNING: lump[{li}] index {g0+gi} -> geom_idx {geom_idx} out of range (gc={gc})")
                    else:
                        print(f"    WARNING: lump[{li}] g0+gi={g0+gi} out of index range (ic={ic})")

            # Trace through body's direct geoms
            for gi in range(b['gc']):
                idx_pos = b['g0'] + gi
                if idx_pos < ic:
                    geom_idx = idx_array[idx_pos]
                    if geom_idx < gc:
                        mi = geoms[geom_idx]['mi']
                        if mi not in mtrl_geoms:
                            mtrl_geoms[mi] = []
                        mtrl_geoms[mi].append(('direct', geom_idx))

            for mi in sorted(mtrl_geoms.keys()):
                mname = materials[mi]['name'] if mi < mc else '???'
                geom_list = mtrl_geoms[mi]
                print(f"    material[{mi}] {mname}: {len(geom_list)} geoms reachable")
                if len(geom_list) <= 20:
                    for src, gidx in geom_list:
                        g = geoms[gidx]
                        print(f"      from lump/src={src}, geom[{gidx}] oi={g['oi']} oj={g['oj']} ok={g['ok']}")

            # Check which materials are NOT reachable
            unreachable = []
            for mi in range(mc):
                if mi in geom_per_mtrl and mi not in mtrl_geoms:
                    unreachable.append(mi)
            if unreachable:
                print(f"    UNREACHABLE materials (have geoms in file but not in body):")
                for mi in unreachable:
                    mname = materials[mi]['name'] if mi < mc else '???'
                    print(f"      material[{mi}] {mname}: {len(geom_per_mtrl[mi])} geoms in file, 0 in body")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Default to 01_easy.sol in data dir
        base = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base, 'data', 'map-putt', '01_easy.sol')
    dump_sol(filepath)
