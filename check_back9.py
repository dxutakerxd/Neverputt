#!/usr/bin/env python3
"""Check all back-9 holes (10-18) of Tricky Golf for SOL corruption."""

import struct
import re
import os

SOL_VERSION_1_6 = 7
M_ALPHA_TEST = 1 << 9
P_ORIENTED = 1
PATHMAX = 64


def read_int(f):
    return struct.unpack('<i', f.read(4))[0]


def skip_to_goal_end(f):
    magic = read_int(f)
    version = read_int(f)
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
            f.read(4 * 4)
    for _ in range(bc):
        f.read(4)
        if version >= SOL_VERSION_1_6:
            f.read(4)
        f.read(4 * 5)
    f.read(hc * 20)
    f.read(zc * 16)
    return f.tell(), counts


def parse_map_entities(mapf):
    if not os.path.exists(mapf):
        return {}
    with open(mapf, 'r', encoding='latin-1') as f:
        content = f.read()
    entities = {}
    for m in re.finditer(r'//\s*entity\s+(\d+)\s*\n\{([^}]*)\}', content):
        eid = int(m.group(1))
        props = {}
        for line in m.group(2).strip().split('\n'):
            pm = re.match(r'\s*"(\w+)"\s+"(.+)"', line)
            if pm:
                props[pm.group(1)] = pm.group(2)
        entities[eid] = props
    return entities


def get_targets(entities):
    targets = {}
    for eid, props in entities.items():
        tn = props.get('targetname', '')
        if tn and 'origin' in props:
            coords = list(map(float, props['origin'].split()))
            targets[tn] = coords
    return targets


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(base, 'android', 'app', 'src', 'main', 'assets', 'data', 'map-ckk')
    data = os.path.join(base, 'data', 'map-ckk')

    for hole in range(10, 19):
        h = f'{hole:02d}'
        sol_path = os.path.join(assets, f'{h}.sol')
        map_path = os.path.join(data, f'{h}.map')

        if not os.path.exists(sol_path):
            print(f'=== Hole {h}: SOL NOT FOUND ===\n')
            continue

        with open(sol_path, 'rb') as f:
            goal_end, c = skip_to_goal_end(f)

        jc = c['jc']; xc = c['xc']; rc = c['rc']
        uc = c['uc']; wc = c['wc']; zc = c['zc']

        with open(sol_path, 'rb') as f:
            filedata = bytearray(f.read())
        file_size = len(filedata)

        nominal = jc * 28 + xc * 40 + rc * 88 + uc * 16 + wc * 24

        print(f'=== Hole {h}: jc={jc} xc={xc} zc={zc} rc={rc} uc={uc} wc={wc} ===')

        ents = parse_map_entities(map_path)
        targets = get_targets(ents)

        issues = []
        pos = goal_end

        # --- Read goals (check for sentinels we may have missed) ---
        # Already skipped by skip_to_goal_end, but let's note the goal_end offset
        # We start reading from goal_end which is the jump section

        # --- Read jumps with sentinel detection ---
        map_jumps = sorted(
            [(eid, p) for eid, p in ents.items()
             if p.get('classname') == 'target_teleporter'],
            key=lambda x: x[0]
        )

        for ji in range(jc):
            v0, v1 = struct.unpack_from('<2i', filedata, pos)
            sentinel = (v0 == -1 and v1 == -1)
            if sentinel:
                issues.append(f'Jump[{ji}] SENTINEL at offset {pos}')
                pos += 8

            jp = struct.unpack_from('<3f', filedata, pos)
            jq = struct.unpack_from('<3f', filedata, pos + 12)
            jr = struct.unpack_from('<f', filedata, pos + 24)[0]

            # Check against MAP
            if ji < len(map_jumps):
                eid, props = map_jumps[ji]
                ox, oy, oz = map(float, props['origin'].split())
                ep = (ox / 64, oz / 64, -oy / 64)
                mr = float(props.get('radius', '0.5'))
                tgt = props.get('target', '')
                eq = None
                if tgt in targets:
                    tx, ty, tz = targets[tgt]
                    eq = (tx / 64, tz / 64, -ty / 64)

                p_ok = all(abs(jp[i] - ep[i]) < 0.02 for i in range(3))
                q_ok = eq is not None and all(abs(jq[i] - eq[i]) < 0.02 for i in range(3))
                r_ok = abs(jr - mr) < 0.02

                if not p_ok or not q_ok or not r_ok:
                    parts = []
                    if not p_ok:
                        parts.append(f'p SOL=({jp[0]:.3f},{jp[1]:.3f},{jp[2]:.3f}) MAP=({ep[0]:.3f},{ep[1]:.3f},{ep[2]:.3f})')
                    if not q_ok:
                        if eq:
                            parts.append(f'q SOL=({jq[0]:.3f},{jq[1]:.3f},{jq[2]:.3f}) MAP=({eq[0]:.3f},{eq[1]:.3f},{eq[2]:.3f})')
                        else:
                            parts.append(f'q target "{tgt}" not found')
                    if not r_ok:
                        parts.append(f'r SOL={jr:.4f} MAP={mr:.4f}')
                    issues.append(f'Jump[{ji}] (entity {eid}): {" | ".join(parts)}')
                else:
                    # Print OK jumps briefly
                    pass

            pos += 28

            # Check for ball-extra pair after this jump entry
            if pos + 8 <= file_size:
                peek = struct.unpack_from('<2f', filedata, pos)
                # Ball extras are typically (ball_p0, ball_p1) with small values
                # Check if these 2 floats look like they don't belong to next jump
                if ji < jc - 1:
                    # Next entry should be either a sentinel or jump p[0]
                    nv0, nv1 = struct.unpack_from('<2i', filedata, pos)
                    if nv0 != -1 or nv1 != -1:
                        # Not a sentinel, should be jump p[0], p[1]
                        pass  # Will be caught by next iteration
                # After last jump, check for stray floats
                elif ji == jc - 1:
                    # Peek at what follows - should be switch sentinel or switch data or ball data
                    pass

        # --- Read switches with sentinel detection ---
        map_switches = sorted(
            [(eid, p) for eid, p in ents.items()
             if p.get('classname') == 'info_camp'],
            key=lambda x: x[0]
        )

        for xi in range(xc):
            v0, v1 = struct.unpack_from('<2i', filedata, pos)
            sentinel = (v0 == -1 and v1 == -1)
            if sentinel:
                issues.append(f'Swch[{xi}] SENTINEL at offset {pos}')
                pos += 8

            sp = struct.unpack_from('<3f', filedata, pos)
            sr = struct.unpack_from('<f', filedata, pos + 12)[0]
            spi = struct.unpack_from('<i', filedata, pos + 16)[0]
            st = struct.unpack_from('<f', filedata, pos + 20)[0]
            st0 = struct.unpack_from('<f', filedata, pos + 24)[0]
            sf = struct.unpack_from('<i', filedata, pos + 28)[0]
            se = struct.unpack_from('<i', filedata, pos + 32)[0]
            si = struct.unpack_from('<i', filedata, pos + 36)[0]

            if sf not in (0, 1):
                issues.append(f'Swch[{xi}] f={sf} (garbage, should be 0 or 1)')
            if si not in (0, 1):
                issues.append(f'Swch[{xi}] i={si} (garbage, should be 0 or 1)')
            if se not in (0, 1):
                issues.append(f'Swch[{xi}] e={se} (garbage, should be 0 or 1)')

            pos += 40

        # --- Skip billboards ---
        pos += rc * 88

        # --- Read balls ---
        ball_pos = pos
        balls_raw = []
        for bi in range(uc):
            bp = struct.unpack_from('<4f', filedata, pos)
            balls_raw.append(bp)
            pos += 16

        # --- Check for extra bytes before views ---
        # Scan forward to find valid view data
        actual_view = None
        scan_end = min(pos + 256, file_size - wc * 24)
        for probe in range(pos, scan_end, 4):
            ok = True
            for vi in range(wc):
                if probe + vi * 24 + 24 > file_size:
                    ok = False
                    break
                vp = struct.unpack_from('<6f', filedata, probe + vi * 24)
                for val in vp:
                    if abs(val) > 2000 or val != val:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                iv_check = probe + wc * 24
                if iv_check + 8 <= file_size:
                    i0, i1 = struct.unpack_from('<2i', filedata, iv_check)
                    if 0 <= i0 < 10000 and 0 <= i1 < 10000:
                        actual_view = probe
                        break

        extra_ball_bytes = (actual_view - pos) if actual_view else 0
        if extra_ball_bytes > 0:
            extra_data = struct.unpack_from(f'<{extra_ball_bytes // 4}f', filedata, pos)
            issues.append(f'{extra_ball_bytes} extra bytes after balls at {pos}: {tuple(f"{v:.4f}" for v in extra_data)}')

        # --- Check ball positions against MAP ---
        map_balls = sorted(
            [(eid, p) for eid, p in ents.items()
             if p.get('classname') == 'info_player_start'],
            key=lambda x: x[0]
        )
        if map_balls:
            eid, props = map_balls[0]
            ox, oy, oz = map(float, props['origin'].split())
            mr = float(props.get('radius', '0.0625'))
            ep = (ox / 64, (oz - 24) / 64 + mr + 0.0005, -oy / 64)

            b = balls_raw[0]
            p_ok = all(abs(b[i] - ep[i]) < 0.02 for i in range(3)) and abs(b[3] - mr) < 0.02
            if not p_ok:
                issues.append(
                    f'Ball[0]: SOL=({b[0]:.4f},{b[1]:.4f},{b[2]:.4f}) r={b[3]:.4f} '
                    f'MAP=({ep[0]:.4f},{ep[1]:.4f},{ep[2]:.4f}) r={mr:.4f}'
                )

        # --- Read views and check against MAP ---
        view_pos = actual_view if actual_view else pos
        map_views = sorted(
            [(eid, p) for eid, p in ents.items()
             if p.get('classname') == 'info_player_intermission'],
            key=lambda x: x[0]
        )
        for wi in range(wc):
            vp = struct.unpack_from('<6f', filedata, view_pos + wi * 24)
            if wi < len(map_views):
                eid, props = map_views[wi]
                ox, oy, oz = map(float, props['origin'].split())
                vep = (ox / 64, oz / 64, -oy / 64)
                tgt = props.get('target', '')
                veq = None
                if tgt in targets:
                    tx, ty, tz = targets[tgt]
                    veq = (tx / 64, tz / 64, -ty / 64)

                vp_ok = all(abs(vp[i] - vep[i]) < 0.05 for i in range(3))
                vq_ok = veq is not None and all(abs(vp[3 + i] - veq[i]) < 0.05 for i in range(3))
                if not vp_ok or not vq_ok:
                    parts = []
                    if not vp_ok:
                        parts.append(f'p SOL=({vp[0]:.3f},{vp[1]:.3f},{vp[2]:.3f}) MAP=({vep[0]:.3f},{vep[1]:.3f},{vep[2]:.3f})')
                    if not vq_ok:
                        if veq:
                            parts.append(f'q SOL=({vp[3]:.3f},{vp[4]:.3f},{vp[5]:.3f}) MAP=({veq[0]:.3f},{veq[1]:.3f},{veq[2]:.3f})')
                    issues.append(f'View[{wi}] (entity {eid}): {" | ".join(parts)}')

        # --- Total extra bytes ---
        total_extra = 0
        # Count sentinel bytes
        p2 = goal_end
        for ji in range(jc):
            v0, v1 = struct.unpack_from('<2i', filedata, p2)
            if v0 == -1 and v1 == -1:
                total_extra += 8
                p2 += 8
            p2 += 28
        for xi in range(xc):
            v0, v1 = struct.unpack_from('<2i', filedata, p2)
            if v0 == -1 and v1 == -1:
                total_extra += 8
                p2 += 8
            p2 += 40
        total_extra += extra_ball_bytes

        if total_extra > 0:
            iv_actual = actual_view + wc * 24 if actual_view else None
            issues.append(f'Total extra bytes in region: {total_extra} (sentinels + ball extras)')

        # --- Print results ---
        if issues:
            for iss in issues:
                print(f'  ** {iss}')
        else:
            print(f'  OK')
        print()


if __name__ == '__main__':
    main()
