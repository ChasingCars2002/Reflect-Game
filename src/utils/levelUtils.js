export function emptyPlayerCells() {
  return Array.from({ length: 5 }, () => Array(5).fill(null))
}

/**
 * Parse the raw 5x5 grid array into a structured object.
 * Returns { cells: [[{type, variant}]], source: {row,col,dir}, target: {row,col} }
 */
export function parseGrid(rawGrid) {
  const SOURCE_DIR = { '>': 'E', '<': 'W', '^': 'N', 'v': 'S' }
  let source = null
  let target = null

  const cells = rawGrid.map((row, r) =>
    row.map((cell, c) => {
      if (!cell || cell === '.') return { type: 'empty', variant: null }

      if (cell.startsWith('S') && cell.length === 2) {
        const dir = SOURCE_DIR[cell[1]]
        source = { row: r, col: c, dir }
        return { type: 'source', variant: dir }
      }
      if (cell === 'T') {
        target = { row: r, col: c }
        return { type: 'target', variant: null }
      }
      if (cell === 'X') return { type: 'obstacle', variant: null }
      if (cell === 'F/') return { type: 'fixed_mirror', variant: '/' }
      if (cell === 'F\\') return { type: 'fixed_mirror', variant: '\\' }
      return { type: 'empty', variant: null }
    })
  )

  return { cells, source, target }
}
