#!/usr/bin/env python3
"""
Fix ball positions in Neverputt SOL files.

The pre-compiled SOL files in this drodin fork have ball X and Z coordinates
negated compared to what the MAP source files specify. This script parses each
SOL file, finds the ball data, negates X and Z to fix the positions, and also
clears the NaN corruption in ball 0.
"""

import struct
import os
import glob
import sys

SOL_VERSION_1_6 = 7
M_ALPHA_TEST = 1 << 9
P_ORIENTED = 1
PATHMAX = 64

def read_int(f):
    return struct.unpack('<i', f.read(4))[0]

def read_float(f):
    return struct.unpack('<f', f.read(4))[0]

def read_floats(f, n):
    return struct.unpack(f'<{n}f', f.read(4 * n))

def write_float(f, val):
    f.write(struct.pack('<f', val))

def parse_sol_to_ball_offset(filepath):
    """Parse SOL file and return (ball_offset, ball_count, version)."""
    with open(filepath, 'rb') as f:
        # Read magic and version
        magic = read_int(f)
        version = read_int(f)

        expected_magic = 0xAF | (ord('S') << 8) | (ord('O') << 16) | (ord('L') << 24)
        if magic != expected_magic:
            return None

        # Read index (counts)
        ac = read_int(f)  # text
        dc = read_int(f)  # dict
        mc = read_int(f)  # material
        vc = read_int(f)  # vert
        ec = read_int(f)  # edge
        sc = read_int(f)  # side
        tc = read_int(f)  # texc

        if version >= SOL_VERSION_1_6:
            oc = read_int(f)  # offs
        else:
            oc = 0

        gc = read_int(f)  # geom
        lc = read_int(f)  # lump
        nc = read_int(f)  # node
        pc = read_int(f)  # path
        bc = read_int(f)  # body
        hc = read_int(f)  # item
        zc = read_int(f)  # goal
        jc = read_int(f)  # jump
        xc = read_int(f)  # swch
        rc = read_int(f)  # bill
        uc = read_int(f)  # ball
        wc = read_int(f)  # view
        ic = read_int(f)  # index

        if uc == 0:
            return None

        # Skip text data
        f.read(ac)

        # Skip dicts: 2 ints each = 8 bytes
        f.read(dc * 8)

        # Skip materials: variable size due to alpha test flag
        for i in range(mc):
            f.read(4 * 4)   # d[4]
            f.read(4 * 4)   # a[4]
            f.read(4 * 4)   # s[4]
            f.read(4 * 4)   # e[4]
            f.read(4 * 1)   # h[1]
            fl = read_int(f)  # fl
            f.read(PATHMAX)   # filename
            if version >= SOL_VERSION_1_6:
                if fl & M_ALPHA_TEST:
                    f.read(4)  # alpha_func
                    f.read(4)  # alpha_ref

        # Skip vertices: 3 floats = 12 bytes each
        f.read(vc * 12)

        # Skip edges: 2 ints = 8 bytes each
        f.read(ec * 8)

        # Skip sides: 3 floats + 1 float = 16 bytes each
        f.read(sc * 16)

        # Skip texcoords: 2 floats = 8 bytes each
        f.read(tc * 8)

        # Skip offsets: 3 ints = 12 bytes each (only if version >= 1.6)
        if version >= SOL_VERSION_1_6:
            f.read(oc * 12)

        # Skip geoms: version dependent
        if version >= SOL_VERSION_1_6:
            f.read(gc * 16)  # 4 ints
        else:
            # Old format: 1 int + 3*(3 ints) = 40 bytes per geom
            f.read(gc * 40)

        # Skip lumps: 9 ints = 36 bytes each
        f.read(lc * 36)

        # Skip nodes: 5 ints = 20 bytes each
        f.read(nc * 20)

        # Skip paths: variable size due to P_ORIENTED flag
        for i in range(pc):
            f.read(4 * 3)   # p[3]
            f.read(4)        # t
            f.read(4)        # pi
            f.read(4)        # f
            f.read(4)        # s
            fl = 0
            if version >= SOL_VERSION_1_6:
                fl = read_int(f)  # fl
            if fl & P_ORIENTED:
                f.read(4 * 4)    # e[4] quaternion

        # Skip bodies: version dependent
        for i in range(bc):
            f.read(4)        # pi
            if version >= SOL_VERSION_1_6:
                f.read(4)    # pj
            f.read(4)        # ni
            f.read(4)        # l0
            f.read(4)        # lc
            f.read(4)        # g0
            f.read(4)        # gc

        # Skip items: 3 floats + 2 ints = 20 bytes each
        f.read(hc * 20)

        # Skip goals: 3 floats + 1 float = 16 bytes each
        f.read(zc * 16)

        # Skip jumps: 6 floats + 1 float = 28 bytes each
        f.read(jc * 28)

        # Skip switches: 3 floats + 1 float + 5 ints/floats = 40 bytes each
        f.read(xc * 40)

        # Skip billboards: 2 ints + 2 floats + 6*3 floats = 88 bytes each
        f.read(rc * 88)

        # NOW we're at ball data!
        ball_offset = f.tell()

        return (ball_offset, uc, version)


def fix_sol_balls(filepath, map_filepath=None):
    """Fix ball positions in a SOL file by computing correct positions from MAP."""
    result = parse_sol_to_ball_offset(filepath)
    if result is None:
        return False

    ball_offset, uc, version = result

    # Read ball origins from MAP file if available
    map_balls = []
    if map_filepath and os.path.exists(map_filepath):
        with open(map_filepath, 'r', encoding='latin-1') as mf:
            lines = mf.readlines()
            in_entity = False
            is_ball = False
            origin = None
            radius = 0.25
            for line in lines:
                line = line.strip()
                if line == '{':
                    in_entity = True
                    is_ball = False
                    origin = None
                    radius = 0.25
                elif line == '}':
                    if is_ball and origin:
                        x, y, z = origin
                        # Apply mapc coordinate conversion
                        SCALE = 64.0
                        SMALL = 0.0005
                        px = x / SCALE
                        py = (z - 24.0) / SCALE
                        pz = -y / SCALE
                        py += radius + SMALL
                        map_balls.append((px, py, pz, radius))
                    in_entity = False
                elif in_entity:
                    if '"classname" "info_player_start"' in line:
                        is_ball = True
                    if '"origin"' in line:
                        parts = line.split('"')
                        if len(parts) >= 4:
                            coords = parts[3].split()
                            if len(coords) == 3:
                                origin = (float(coords[0]), float(coords[1]), float(coords[2]))
                    if '"radius"' in line:
                        parts = line.split('"')
                        if len(parts) >= 4:
                            radius = float(parts[3])

    # Verify our offset against what we know
    with open(filepath, 'rb') as f:
        f.seek(ball_offset)
        balls = []
        for i in range(uc):
            px, py, pz = read_floats(f, 3)
            r = read_float(f)
            balls.append((px, py, pz, r))

    print(f"  File: {filepath}")
    print(f"  Ball offset: {ball_offset}, Count: {uc}")
    for i, (px, py, pz, r) in enumerate(balls):
        print(f"    Ball[{i}]: ({px:.4f}, {py:.4f}, {pz:.4f}) r={r:.4f}")

    # Compute fixed ball data
    fixed_balls = []
    if map_balls:
        print(f"  MAP balls available: {len(map_balls)}")
        for i in range(uc):
            if i < len(map_balls):
                fixed_balls.append(map_balls[i])
                print(f"    Fixed[{i}] from MAP: ({map_balls[i][0]:.4f}, {map_balls[i][1]:.4f}, {map_balls[i][2]:.4f}) r={map_balls[i][3]:.4f}")
            else:
                # Use last MAP ball if we have fewer MAP entries
                fixed_balls.append(map_balls[-1])
    else:
        # No MAP file - just negate X and Z for non-NaN balls
        # For ball 0 (typically NaN), use ball 1's data with negated X/Z
        for i in range(uc):
            px, py, pz, r = balls[i]
            if i == 0 and uc > 1:
                # Ball 0 is corrupted (NaN), copy from ball 1 with fix
                px1, py1, pz1, r1 = balls[1]
                fixed_balls.append((-px1, py1, -pz1, r1))
            else:
                fixed_balls.append((-px, py, -pz, r))
        for i, (px, py, pz, r) in enumerate(fixed_balls):
            print(f"    Fixed[{i}] (negate X,Z): ({px:.4f}, {py:.4f}, {pz:.4f}) r={r:.4f}")

    # Write fixed ball data
    with open(filepath, 'r+b') as f:
        f.seek(ball_offset)
        for px, py, pz, r in fixed_balls:
            write_float(f, px)
            write_float(f, py)
            write_float(f, pz)
            write_float(f, r)

    print(f"  PATCHED {uc} balls")
    return True


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    assets_dir = os.path.join(base_dir, 'android', 'app', 'src', 'main', 'assets', 'data')

    # Find all SOL files that have corresponding MAP files (course files)
    sol_files = []
    for d in [data_dir, assets_dir]:
        for sol_path in glob.glob(os.path.join(d, 'map-*', '*.sol')):
            map_path = sol_path.replace('.sol', '.map')
            sol_files.append((sol_path, map_path if os.path.exists(map_path) else None))

    if not sol_files:
        print("No SOL files found!")
        return

    print(f"Found {len(sol_files)} SOL files to process\n")

    fixed = 0
    for sol_path, map_path in sorted(sol_files):
        rel = os.path.relpath(sol_path, base_dir)
        print(f"\nProcessing: {rel}")
        if fix_sol_balls(sol_path, map_path):
            fixed += 1

    print(f"\n{'='*60}")
    print(f"Fixed {fixed} SOL files")


if __name__ == '__main__':
    main()
