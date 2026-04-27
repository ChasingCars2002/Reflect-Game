const DIRS = {
  N: { dr: -1, dc: 0 },
  S: { dr: 1, dc: 0 },
  E: { dr: 0, dc: 1 },
  W: { dr: 0, dc: -1 },
}

const SOURCE_DIR = { '>': 'E', '<': 'W', '^': 'N', 'v': 'S' }

// Reflection tables
const REFLECT_SLASH = { N: 'E', E: 'N', S: 'W', W: 'S' }
const REFLECT_BSLASH = { N: 'W', W: 'N', S: 'E', E: 'S' }

/**
 * Simulate the light beam on a 5x5 grid.
 *
 * @param {string[][]} grid        - 5x5 base grid (seed cells)
 * @param {(string|null)[][]} playerCells - 5x5 overlay of player-placed mirrors ("M/" | "M\\" | null)
 * @returns {{ path: {row:number, col:number, dir:string}[], solved: boolean, loop: boolean }}
 */
export function traceBeam(grid, playerCells) {
  // Locate source
  let startRow = -1, startCol = -1, startDir = null
  outer:
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      const cell = grid[r][c]
      if (cell && cell.startsWith('S') && cell.length === 2) {
        startRow = r
        startCol = c
        startDir = SOURCE_DIR[cell[1]]
        break outer
      }
    }
  }

  if (startDir === null) return { path: [], solved: false, loop: false }

  let row = startRow
  let col = startCol
  let dir = startDir
  const visited = new Set()
  const path = []

  while (true) {
    const { dr, dc } = DIRS[dir]
    const nr = row + dr
    const nc = col + dc

    // Out of bounds
    if (nr < 0 || nr > 4 || nc < 0 || nc > 4) {
      return { path, solved: false, loop: false }
    }

    const key = `${nr},${nc},${dir}`
    if (visited.has(key)) {
      return { path, solved: false, loop: true }
    }
    visited.add(key)
    path.push({ row: nr, col: nc, dir })

    // Player cell takes priority
    const content = (playerCells[nr][nc] !== null && playerCells[nr][nc] !== undefined)
      ? playerCells[nr][nc]
      : grid[nr][nc]

    if (content === 'T') {
      return { path, solved: true, loop: false }
    } else if (content === 'X' || (typeof content === 'string' && content.startsWith('S'))) {
      return { path, solved: false, loop: false }
    } else if (content === 'F/' || content === 'M/') {
      dir = REFLECT_SLASH[dir]
    } else if (content === 'F\\' || content === 'M\\') {
      dir = REFLECT_BSLASH[dir]
    }
    // '.' — continue straight

    row = nr
    col = nc
  }
}
