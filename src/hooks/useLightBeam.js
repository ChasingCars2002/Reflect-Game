import { useMemo } from 'react'
import { traceBeam } from '../utils/rayTracer'

export function useLightBeam(grid, playerCells) {
  return useMemo(() => traceBeam(grid, playerCells), [grid, playerCells])
}
