import { useCallback, useEffect, useMemo, useState } from 'react'
import { traceBeam } from '../utils/rayTracer'
import { emptyPlayerCells, parseGrid } from '../utils/levelUtils'

/**
 * Central game state for a single level.
 * Manages playerCells, inventory, win state, and exposes mutators.
 */
export function useGameState(levelData) {
  const grid = levelData.grid
  const initialInventory = levelData.inventory

  const parsed = useMemo(() => parseGrid(grid), [grid])

  const [playerCells, setPlayerCells] = useState(() => emptyPlayerCells(grid.length))
  const [inventory, setInventory] = useState(initialInventory)

  // Reset state whenever the level changes
  useEffect(() => {
    setPlayerCells(emptyPlayerCells(grid.length))
    setInventory(initialInventory)
  }, [levelData.id, initialInventory])

  const beam = useMemo(() => traceBeam(grid, playerCells), [grid, playerCells])
  const won = beam.solved

  const cellIsPlaceable = useCallback(
    (row, col) => {
      // Must be empty in the base grid AND empty in player overlay
      return grid[row][col] === '.' && playerCells[row][col] === null
    },
    [grid, playerCells]
  )

  const placeMirror = useCallback(
    (row, col, type) => {
      if (!(grid[row][col] === '.')) return false
      if (playerCells[row][col] !== null) return false
      if (inventory <= 0) return false
      setPlayerCells((prev) => {
        const next = prev.map((r) => r.slice())
        next[row][col] = `M${type}`
        return next
      })
      setInventory((n) => n - 1)
      return true
    },
    [grid, playerCells, inventory]
  )

  const removeMirror = useCallback(
    (row, col) => {
      if (playerCells[row][col] === null) return false
      setPlayerCells((prev) => {
        const next = prev.map((r) => r.slice())
        next[row][col] = null
        return next
      })
      setInventory((n) => n + 1)
      return true
    },
    [playerCells]
  )

  const rotateMirror = useCallback(
    (row, col) => {
      const cur = playerCells[row][col]
      if (cur !== 'M/' && cur !== 'M\\') return false
      const next = cur === 'M/' ? 'M\\' : 'M/'
      setPlayerCells((prev) => {
        const copy = prev.map((r) => r.slice())
        copy[row][col] = next
        return copy
      })
      return true
    },
    [playerCells]
  )

  const moveMirror = useCallback(
    (fromRow, fromCol, toRow, toCol, type) => {
      if (fromRow === toRow && fromCol === toCol) return false
      if (grid[toRow][toCol] !== '.') return false
      if (playerCells[toRow][toCol] !== null) return false
      if (playerCells[fromRow][fromCol] === null) return false
      setPlayerCells((prev) => {
        const next = prev.map((r) => r.slice())
        next[fromRow][fromCol] = null
        next[toRow][toCol] = `M${type}`
        return next
      })
      return true
    },
    [grid, playerCells]
  )

  const resetLevel = useCallback(() => {
    setPlayerCells(emptyPlayerCells(grid.length))
    setInventory(initialInventory)
  }, [grid.length, initialInventory])

  return {
    parsed,
    grid,
    playerCells,
    inventory,
    initialInventory,
    beam,
    won,
    cellIsPlaceable,
    placeMirror,
    removeMirror,
    rotateMirror,
    moveMirror,
    resetLevel,
  }
}
