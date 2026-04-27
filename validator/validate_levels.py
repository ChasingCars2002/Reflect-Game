"""
Reflect — Level Validator and Generator
========================================

Validates JSON level seeds for the Reflect puzzle game and generates
new seeds.

Usage:
    python validate_levels.py validate seeds.json
    python validate_levels.py generate <count> <output.json>
    python validate_levels.py generate-50            # writes seeds.json with 50 levels
"""

from __future__ import annotations
import json
import random
import sys
from itertools import combinations, product
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Beam simulation (mirror of src/utils/rayTracer.js)
# ---------------------------------------------------------------------------

DIRS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
SOURCE_DIR = {">": "E", "<": "W", "^": "N", "v": "S"}
SLASH = {"N": "E", "E": "N", "S": "W", "W": "S"}
BSLASH = {"N": "W", "W": "N", "S": "E", "E": "S"}

GRID_N = 5  # 5x5


def find_source(grid):
    for r in range(GRID_N):
        for c in range(GRID_N):
            cell = grid[r][c]
            if isinstance(cell, str) and len(cell) == 2 and cell[0] == "S":
                return r, c, SOURCE_DIR[cell[1]]
    return None


def find_target(grid):
    for r in range(GRID_N):
        for c in range(GRID_N):
            if grid[r][c] == "T":
                return r, c
    return None


def trace_beam(grid, player):
    """
    grid: 5x5 list of cell strings
    player: dict {(r,c): "M/" or "M\\"} of player-placed mirrors
    Returns (solved: bool, path: list[(r,c,dir)])
    """
    src = find_source(grid)
    if src is None:
        return False, []
    r, c, direction = src
    visited = set()
    path = []

    while True:
        dr, dc = DIRS[direction]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < GRID_N and 0 <= nc < GRID_N):
            return False, path

        key = (nr, nc, direction)
        if key in visited:
            return False, path
        visited.add(key)
        path.append(key)

        content = player.get((nr, nc), grid[nr][nc])
        if content == "T":
            return True, path
        if content == "X" or (isinstance(content, str) and content.startswith("S")):
            return False, path
        if content in ("F/", "M/"):
            direction = SLASH[direction]
        elif content in ("F\\", "M\\"):
            direction = BSLASH[direction]
        # "." continues straight

        r, c = nr, nc


# ---------------------------------------------------------------------------
# Solvability
# ---------------------------------------------------------------------------

def empty_cells(grid):
    return [(r, c) for r in range(GRID_N) for c in range(GRID_N) if grid[r][c] == "."]


def find_solution(level):
    """
    Search for a placement of UP TO `inventory` mirrors on empty cells
    that solves the puzzle. Returns (solvable, mirrors_used, placement).
    """
    grid = level["grid"]
    n = level["inventory"]
    if find_source(grid) is None or find_target(grid) is None:
        return False, 0, None

    empties = empty_cells(grid)

    # Try k=0..n (zero-mirror solution would mean trivial)
    for k in range(0, n + 1):
        if k > len(empties):
            break
        for positions in combinations(empties, k):
            for types in product(("/", "\\"), repeat=k):
                player = {pos: f"M{t}" for pos, t in zip(positions, types)}
                solved, _ = trace_beam(grid, player)
                if solved:
                    return True, k, player
    return False, 0, None


def find_min_mirror_solution(level, max_mirrors):
    """Same as find_solution but only checks up to max_mirrors."""
    grid = level["grid"]
    if find_source(grid) is None or find_target(grid) is None:
        return False, 0, None
    empties = empty_cells(grid)
    for k in range(0, max_mirrors + 1):
        if k > len(empties):
            break
        for positions in combinations(empties, k):
            for types in product(("/", "\\"), repeat=k):
                player = {pos: f"M{t}" for pos, t in zip(positions, types)}
                solved, _ = trace_beam(grid, player)
                if solved:
                    return True, k, player
    return False, 0, None


# ---------------------------------------------------------------------------
# D4 symmetry — uniqueness check
# ---------------------------------------------------------------------------

# When the grid is rotated/reflected, mirror types may flip.
# `/` and `\` swap under: 90° rotation, 270° rotation, horizontal reflection,
# vertical reflection. They are preserved under: identity, 180° rotation,
# main-diagonal reflection, anti-diagonal reflection.
#
# For the source direction, we also need to remap N/S/E/W under each transform.

N1 = GRID_N - 1


def _t_identity(r, c): return (r, c)
def _t_rot90(r, c): return (c, N1 - r)
def _t_rot180(r, c): return (N1 - r, N1 - c)
def _t_rot270(r, c): return (N1 - c, r)
def _t_refh(r, c): return (r, N1 - c)
def _t_refv(r, c): return (N1 - r, c)
def _t_refd(r, c): return (c, r)
def _t_refa(r, c): return (N1 - c, N1 - r)


# Each entry: (coord_transform, swap_mirror_type, dir_remap)
# dir_remap maps the OLD direction symbol to the NEW one after the transform.
TRANSFORMS = [
    (_t_identity, False, {"N": "N", "S": "S", "E": "E", "W": "W"}),
    (_t_rot90,    True,  {"N": "E", "E": "S", "S": "W", "W": "N"}),
    (_t_rot180,   False, {"N": "S", "S": "N", "E": "W", "W": "E"}),
    (_t_rot270,   True,  {"N": "W", "W": "S", "S": "E", "E": "N"}),
    (_t_refh,     True,  {"N": "N", "S": "S", "E": "W", "W": "E"}),
    (_t_refv,     True,  {"N": "S", "S": "N", "E": "E", "W": "W"}),
    (_t_refd,     False, {"N": "W", "W": "N", "S": "E", "E": "S"}),
    (_t_refa,     False, {"N": "E", "E": "N", "S": "W", "W": "S"}),
]

DIR_TO_SOURCE_CHAR = {"N": "^", "S": "v", "E": ">", "W": "<"}


def transform_cell(cell, swap_mirror, dir_remap):
    if cell in (".", "T", "X"):
        return cell
    if cell.startswith("S") and len(cell) == 2:
        old_dir = SOURCE_DIR[cell[1]]
        new_dir = dir_remap[old_dir]
        return "S" + DIR_TO_SOURCE_CHAR[new_dir]
    if cell == "F/":
        return "F\\" if swap_mirror else "F/"
    if cell == "F\\":
        return "F/" if swap_mirror else "F\\"
    if cell == "M/":
        return "M\\" if swap_mirror else "M/"
    if cell == "M\\":
        return "M/" if swap_mirror else "M\\"
    return cell


def transform_grid(grid, coord_fn, swap_mirror, dir_remap):
    new = [["." for _ in range(GRID_N)] for _ in range(GRID_N)]
    for r in range(GRID_N):
        for c in range(GRID_N):
            nr, nc = coord_fn(r, c)
            new[nr][nc] = transform_cell(grid[r][c], swap_mirror, dir_remap)
    return new


def grid_signature(grid, inventory):
    rows = ["|".join(row) for row in grid]
    return f"{inventory}#" + "/".join(rows)


def canonical_signature(level):
    grid = level["grid"]
    inv = level["inventory"]
    sigs = []
    for coord_fn, swap, dir_remap in TRANSFORMS:
        tg = transform_grid(grid, coord_fn, swap, dir_remap)
        sigs.append(grid_signature(tg, inv))
    return min(sigs)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_schema(level):
    if not isinstance(level, dict):
        return "level is not an object"
    for key in ("id", "inventory", "grid"):
        if key not in level:
            return f"missing key '{key}'"
    if not isinstance(level["inventory"], int) or level["inventory"] < 0:
        return "inventory must be non-negative integer"
    grid = level["grid"]
    if not isinstance(grid, list) or len(grid) != GRID_N:
        return f"grid must be {GRID_N} rows"
    for row in grid:
        if not isinstance(row, list) or len(row) != GRID_N:
            return f"each row must be {GRID_N} cells"
        for cell in row:
            if cell not in (
                ".", "T", "X",
                "S>", "S<", "S^", "Sv",
                "F/", "F\\",
            ):
                return f"invalid cell value '{cell}'"
    if find_source(grid) is None:
        return "no source on grid"
    if find_target(grid) is None:
        return "no target on grid"
    return None


def validate_all(seeds_path):
    with open(seeds_path) as f:
        levels = json.load(f)

    seen = {}
    errors = []
    print(f"Validating {len(levels)} levels from {seeds_path}\n")

    for level in levels:
        lid = level.get("id", "?")

        schema_err = validate_schema(level)
        if schema_err:
            errors.append(f"[{lid}] schema: {schema_err}")
            continue

        solvable, k, _ = find_solution(level)
        if not solvable:
            errors.append(f"[{lid}] NOT SOLVABLE with inventory={level['inventory']}")
            continue

        canon = canonical_signature(level)
        if canon in seen:
            errors.append(f"[{lid}] DUPLICATE of [{seen[canon]}]")
            continue
        seen[canon] = lid

        diff = level.get("difficulty", "?")
        print(f"  [{lid}] OK  inv={level['inventory']}  used={k}  diff={diff}")

    print()
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    else:
        print(f"PASSED: all {len(levels)} levels valid and unique.")


# ---------------------------------------------------------------------------
# Seed generation
# ---------------------------------------------------------------------------

SOURCE_SYMBOLS = ["S>", "S<", "S^", "Sv"]


def random_blank_grid():
    return [["." for _ in range(GRID_N)] for _ in range(GRID_N)]


def random_edge_position(rng, side):
    """side in {'N','S','E','W'}; returns (r,c) on that edge."""
    if side == "N": return (0, rng.randrange(GRID_N))
    if side == "S": return (N1, rng.randrange(GRID_N))
    if side == "W": return (rng.randrange(GRID_N), 0)
    if side == "E": return (rng.randrange(GRID_N), N1)


def random_inner_position(rng):
    return (rng.randrange(GRID_N), rng.randrange(GRID_N))


def random_source_pointing_inward(rng):
    side = rng.choice(["N", "S", "E", "W"])
    r, c = random_edge_position(rng, side)
    # Source on edge must point inward
    if side == "N": dir_char = "v"
    elif side == "S": dir_char = "^"
    elif side == "W": dir_char = ">"
    else: dir_char = "<"
    return (r, c, "S" + dir_char)


def generate_candidate(rng, inventory, n_fixed=0, n_obstacles=0):
    """Generate a random grid layout that is solvable with the given inventory."""
    grid = random_blank_grid()
    occupied = set()

    # Place source on an edge pointing inward
    sr, sc, sym = random_source_pointing_inward(rng)
    grid[sr][sc] = sym
    occupied.add((sr, sc))

    # Place target somewhere not equal to source
    while True:
        tr, tc = random_inner_position(rng)
        if (tr, tc) not in occupied:
            grid[tr][tc] = "T"
            occupied.add((tr, tc))
            break

    # Place fixed mirrors
    for _ in range(n_fixed):
        for _try in range(20):
            r, c = random_inner_position(rng)
            if (r, c) not in occupied:
                grid[r][c] = "F" + rng.choice(["/", "\\"])
                occupied.add((r, c))
                break

    # Place obstacles
    for _ in range(n_obstacles):
        for _try in range(20):
            r, c = random_inner_position(rng)
            if (r, c) not in occupied:
                grid[r][c] = "X"
                occupied.add((r, c))
                break

    return {"grid": grid, "inventory": inventory}


def generate_unique_solvable(rng, count, category_specs):
    """
    category_specs is a list of dicts:
      {"count": int, "inventory": int, "fixed": int, "obstacles": int,
       "min_mirrors_used": int, "difficulty": int}

    Returns a list of `count` validated unique levels.
    """
    levels = []
    seen_canon = set()
    next_id = 1

    for spec in category_specs:
        target_count = spec["count"]
        produced = 0
        attempts = 0
        max_attempts = target_count * 4000

        while produced < target_count and attempts < max_attempts:
            attempts += 1
            cand = generate_candidate(
                rng,
                inventory=spec["inventory"],
                n_fixed=spec["fixed"],
                n_obstacles=spec["obstacles"],
            )
            cand["id"] = next_id
            cand["difficulty"] = spec["difficulty"]

            # Quick schema sanity
            if validate_schema(cand) is not None:
                continue

            # Reject trivially solvable (require at least min_mirrors_used)
            min_used = spec.get("min_mirrors_used", 1)
            ok, used, _ = find_min_mirror_solution(cand, cand["inventory"])
            if not ok or used < min_used:
                continue

            canon = canonical_signature(cand)
            if canon in seen_canon:
                continue
            seen_canon.add(canon)

            levels.append(cand)
            next_id += 1
            produced += 1

        if produced < target_count:
            print(
                f"WARNING: category (inv={spec['inventory']}, "
                f"fixed={spec['fixed']}, obs={spec['obstacles']}, "
                f"min_used={spec.get('min_mirrors_used',1)}) only produced "
                f"{produced}/{target_count}",
                file=sys.stderr,
            )

    return levels


def generate_50(output_path, seed=42):
    rng = random.Random(seed)
    specs = [
        # Category A: Beginner — inventory 1, no fixed/obstacles, requires 1 mirror
        {"count": 12, "inventory": 1, "fixed": 0, "obstacles": 0,
         "min_mirrors_used": 1, "difficulty": 1},
        # Category B: Easy — 1 fixed mirror + 1 player mirror
        {"count": 10, "inventory": 1, "fixed": 1, "obstacles": 0,
         "min_mirrors_used": 1, "difficulty": 2},
        # Category C: Medium — 2 player mirrors
        {"count": 10, "inventory": 2, "fixed": 0, "obstacles": 0,
         "min_mirrors_used": 2, "difficulty": 2},
        # Category D: Medium with obstacle
        {"count": 8, "inventory": 2, "fixed": 0, "obstacles": 1,
         "min_mirrors_used": 2, "difficulty": 3},
        # Category E: Hard, 3 mirrors
        {"count": 6, "inventory": 3, "fixed": 0, "obstacles": 1,
         "min_mirrors_used": 3, "difficulty": 3},
        # Category F: Expert
        {"count": 4, "inventory": 3, "fixed": 1, "obstacles": 1,
         "min_mirrors_used": 3, "difficulty": 4},
    ]
    levels = generate_unique_solvable(rng, 50, specs)
    print(f"Generated {len(levels)} unique solvable levels.")

    # Re-id sequentially 1..N
    for i, lvl in enumerate(levels, start=1):
        lvl["id"] = i
        lvl["title"] = f"Level {i}"

    with open(output_path, "w") as f:
        json.dump(levels, f, indent=2)
    print(f"Wrote {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    here = Path(__file__).parent

    if cmd == "validate":
        path = sys.argv[2] if len(sys.argv) > 2 else str(here / "seeds.json")
        validate_all(path)
    elif cmd == "generate":
        count = int(sys.argv[2])
        out = sys.argv[3]
        rng = random.Random(0)
        # Fall back to a single category
        specs = [{"count": count, "inventory": 2, "fixed": 0, "obstacles": 0,
                  "min_mirrors_used": 1, "difficulty": 2}]
        levels = generate_unique_solvable(rng, count, specs)
        for i, lvl in enumerate(levels, start=1):
            lvl["id"] = i
            lvl["title"] = f"Level {i}"
        with open(out, "w") as f:
            json.dump(levels, f, indent=2)
        print(f"Wrote {len(levels)} levels to {out}")
    elif cmd == "generate-50":
        out = str(here / "seeds.json")
        generate_50(out)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
