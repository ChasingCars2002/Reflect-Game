"""
Reflect — Level Validator and Generator
========================================

Validates JSON level seeds for the Reflect puzzle game and generates
new seeds.

Usage:
    python validate_levels.py validate seeds.json
    python validate_levels.py generate <count> <output.json>
    python validate_levels.py generate-all            # writes seeds.json with 50 levels
"""

from __future__ import annotations
import json
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Beam simulation (mirror of src/utils/rayTracer.js)
# ---------------------------------------------------------------------------

DIRS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
SOURCE_DIR = {">": "E", "<": "W", "^": "N", "v": "S"}
SLASH = {"N": "E", "E": "N", "S": "W", "W": "S"}
BSLASH = {"N": "W", "W": "N", "S": "E", "E": "S"}


def find_source(grid):
    n = len(grid)
    for r in range(n):
        for c in range(n):
            cell = grid[r][c]
            if isinstance(cell, str) and len(cell) == 2 and cell[0] == "S":
                return r, c, SOURCE_DIR[cell[1]]
    return None


def find_target(grid):
    n = len(grid)
    for r in range(n):
        for c in range(n):
            if grid[r][c] == "T":
                return r, c
    return None


def trace_beam(grid, player):
    n = len(grid)
    src = find_source(grid)
    if src is None:
        return False, []
    r, c, direction = src
    visited = set()
    path = []

    while True:
        dr, dc = DIRS[direction]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < n and 0 <= nc < n):
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

        r, c = nr, nc


# ---------------------------------------------------------------------------
# Solvability — beam-guided DFS with memoisation
# ---------------------------------------------------------------------------

def empty_cells(grid):
    n = len(grid)
    return [(r, c) for r in range(n) for c in range(n) if grid[r][c] == "."]


def find_solution_guided(level):
    """
    Search for a placement of UP TO `inventory` mirrors on empty cells that
    solves the puzzle. Uses beam-guided DFS: only considers placing mirrors
    on cells the current beam travels through, since only those can redirect
    the beam. Returns (solvable, mirrors_used, placement).
    """
    grid = level["grid"]
    n_inv = level["inventory"]
    if find_source(grid) is None or find_target(grid) is None:
        return False, 0, None

    # memo[frozen_state] = max budget at which we tried this state and failed
    memo = {}

    def dfs(player, budget):
        key = frozenset(player.items())
        # If we already tried this exact state with at least this budget and failed, skip
        if memo.get(key, -1) >= budget:
            return None
        memo[key] = budget

        solved, path = trace_beam(grid, player)
        if solved:
            return player
        if budget == 0:
            return None
        candidates = [
            (r, c) for (r, c, _) in path
            if grid[r][c] == "." and (r, c) not in player
        ]
        for pos in candidates:
            for mtype in ("M/", "M\\"):
                result = dfs({**player, pos: mtype}, budget - 1)
                if result is not None:
                    return result
        return None

    for k in range(0, n_inv + 1):
        result = dfs({}, k)
        if result is not None:
            return True, len(result), result
    return False, 0, None


# ---------------------------------------------------------------------------
# D4 symmetry — uniqueness check
# ---------------------------------------------------------------------------

def make_transforms(n1):
    def _identity(r, c): return (r, c)
    def _rot90(r, c): return (c, n1 - r)
    def _rot180(r, c): return (n1 - r, n1 - c)
    def _rot270(r, c): return (n1 - c, r)
    def _refh(r, c): return (r, n1 - c)
    def _refv(r, c): return (n1 - r, c)
    def _refd(r, c): return (c, r)
    def _refa(r, c): return (n1 - c, n1 - r)
    return [
        (_identity, False, {"N": "N", "S": "S", "E": "E", "W": "W"}),
        (_rot90,    True,  {"N": "E", "E": "S", "S": "W", "W": "N"}),
        (_rot180,   False, {"N": "S", "S": "N", "E": "W", "W": "E"}),
        (_rot270,   True,  {"N": "W", "W": "S", "S": "E", "E": "N"}),
        (_refh,     True,  {"N": "N", "S": "S", "E": "W", "W": "E"}),
        (_refv,     True,  {"N": "S", "S": "N", "E": "E", "W": "W"}),
        (_refd,     False, {"N": "W", "W": "N", "S": "E", "E": "S"}),
        (_refa,     False, {"N": "E", "E": "N", "S": "W", "W": "S"}),
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
    n = len(grid)
    new = [["." for _ in range(n)] for _ in range(n)]
    for r in range(n):
        for c in range(n):
            nr, nc = coord_fn(r, c)
            new[nr][nc] = transform_cell(grid[r][c], swap_mirror, dir_remap)
    return new


def grid_signature(grid, inventory):
    n = len(grid)
    rows = ["|".join(row) for row in grid]
    return f"{inventory}#{n}x" + "/".join(rows)


def canonical_signature(level):
    grid = level["grid"]
    inv = level["inventory"]
    n1 = len(grid) - 1
    sigs = []
    for coord_fn, swap, dir_remap in make_transforms(n1):
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
    if not isinstance(grid, list) or len(grid) not in (5, 7):
        return "grid must be 5×5 or 7×7"
    n = len(grid)
    for row in grid:
        if not isinstance(row, list) or len(row) != n:
            return f"each row must have {n} cells"
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

        solvable, k, _ = find_solution_guided(level)
        if not solvable:
            errors.append(f"[{lid}] NOT SOLVABLE with inventory={level['inventory']}")
            continue

        canon = canonical_signature(level)
        if canon in seen:
            errors.append(f"[{lid}] DUPLICATE of [{seen[canon]}]")
            continue
        seen[canon] = lid

        diff = level.get("difficulty", "?")
        n = len(level["grid"])
        print(f"  [{lid}] OK  grid={n}x{n}  inv={level['inventory']}  used={k}  diff={diff}")

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

def random_blank_grid(n):
    return [["." for _ in range(n)] for _ in range(n)]


def random_edge_position(rng, side, n):
    n1 = n - 1
    if side == "N": return (0, rng.randrange(n))
    if side == "S": return (n1, rng.randrange(n))
    if side == "W": return (rng.randrange(n), 0)
    if side == "E": return (rng.randrange(n), n1)


def random_cell_position(rng, n):
    return (rng.randrange(n), rng.randrange(n))


def random_interior_position(rng, n):
    """Returns a non-edge cell, so the target can't be trivially adjacent to a wall."""
    return (rng.randrange(1, n - 1), rng.randrange(1, n - 1))


def random_source_pointing_inward(rng, n):
    side = rng.choice(["N", "S", "E", "W"])
    r, c = random_edge_position(rng, side, n)
    if side == "N": dir_char = "v"
    elif side == "S": dir_char = "^"
    elif side == "W": dir_char = ">"
    else: dir_char = "<"
    return (r, c, "S" + dir_char)


def generate_candidate(rng, inventory, n_fixed=0, n_obstacles=0, grid_n=5):
    grid = random_blank_grid(grid_n)
    occupied = set()

    sr, sc, sym = random_source_pointing_inward(rng, grid_n)
    grid[sr][sc] = sym
    occupied.add((sr, sc))

    # Place target at an interior cell so the beam must navigate to reach it
    for _ in range(100):
        tr, tc = random_interior_position(rng, grid_n)
        if (tr, tc) not in occupied:
            grid[tr][tc] = "T"
            occupied.add((tr, tc))
            break

    for _ in range(n_fixed):
        for _try in range(20):
            r, c = random_cell_position(rng, grid_n)
            if (r, c) not in occupied:
                grid[r][c] = "F" + rng.choice(["/", "\\"])
                occupied.add((r, c))
                break

    for _ in range(n_obstacles):
        for _try in range(20):
            r, c = random_cell_position(rng, grid_n)
            if (r, c) not in occupied:
                grid[r][c] = "X"
                occupied.add((r, c))
                break

    return {"grid": grid, "inventory": inventory}


def generate_unique_solvable(rng, total_count, category_specs):
    """
    category_specs is a list of dicts:
      {"count": int, "inventory": int, "fixed": int, "obstacles": int,
       "min_mirrors_used": int, "difficulty": int, "grid_n": int}
    """
    levels = []
    seen_canon = set()
    next_id = 1

    for spec in category_specs:
        target_count = spec["count"]
        grid_n = spec.get("grid_n", 5)
        produced = 0
        attempts = 0
        max_attempts = target_count * 8000

        while produced < target_count and attempts < max_attempts:
            attempts += 1
            cand = generate_candidate(
                rng,
                inventory=spec["inventory"],
                n_fixed=spec["fixed"],
                n_obstacles=spec["obstacles"],
                grid_n=grid_n,
            )
            cand["id"] = next_id
            cand["difficulty"] = spec["difficulty"]

            if validate_schema(cand) is not None:
                continue

            min_used = spec.get("min_mirrors_used", 1)
            ok, used, _ = find_solution_guided(cand)
            if not ok or used < min_used:
                continue

            canon = canonical_signature(cand)
            if canon in seen_canon:
                continue
            seen_canon.add(canon)

            levels.append(cand)
            next_id += 1
            produced += 1
            print(
                f"  [{next_id - 1:02d}] inv={spec['inventory']}  used={used}"
                f"  diff={spec['difficulty']}  grid={grid_n}x{grid_n}"
                f"  (attempt {attempts})"
            )

        if produced < target_count:
            print(
                f"WARNING: category (inv={spec['inventory']}, "
                f"fixed={spec['fixed']}, obs={spec['obstacles']}, "
                f"min_used={spec.get('min_mirrors_used', 1)}, grid={grid_n}) "
                f"only produced {produced}/{target_count} after {attempts} attempts",
                file=sys.stderr,
            )

    return levels


def generate_all(output_path, seed=42):
    rng = random.Random(seed)
    specs = [
        # Level 1: easy intro, 5×5
        {"count":  1, "inventory": 1, "fixed": 0, "obstacles": 0,
         "min_mirrors_used": 1, "difficulty": 1, "grid_n": 5},
        # Levels 2–20: hard, 7×7, must use all 4 mirrors
        {"count": 19, "inventory": 4, "fixed": 2, "obstacles": 2,
         "min_mirrors_used": 4, "difficulty": 4, "grid_n": 7},
        # Levels 21–40: expert, 7×7, must use at least 4 of 5 mirrors
        {"count": 20, "inventory": 5, "fixed": 3, "obstacles": 2,
         "min_mirrors_used": 4, "difficulty": 5, "grid_n": 7},
        # Levels 41–50: master, 7×7, 5 mirrors + extra obstacle, at least 4 used
        {"count": 10, "inventory": 5, "fixed": 3, "obstacles": 3,
         "min_mirrors_used": 4, "difficulty": 6, "grid_n": 7},
    ]
    print("Generating 50 levels (1 intro + 49 hard)...\n")
    levels = generate_unique_solvable(rng, 50, specs)
    print(f"\nGenerated {len(levels)} unique solvable levels.")

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
        specs = [{"count": count, "inventory": 2, "fixed": 0, "obstacles": 0,
                  "min_mirrors_used": 1, "difficulty": 2, "grid_n": 5}]
        levels = generate_unique_solvable(rng, count, specs)
        for i, lvl in enumerate(levels, start=1):
            lvl["id"] = i
            lvl["title"] = f"Level {i}"
        with open(out, "w") as f:
            json.dump(levels, f, indent=2)
        print(f"Wrote {len(levels)} levels to {out}")
    elif cmd == "generate-all":
        out = str(here / "seeds.json")
        generate_all(out)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
