import React, { useLayoutEffect, useRef, useState } from 'react'
import Cell from './Cell'
import LightBeam from './LightBeam'

export default function GameBoard({
  parsed,
  playerCells,
  beam,
  inventory,
  won,
  dragHandlers,
  onRotate,
  onRemove,
  gridN,
}) {
  const containerRef = useRef(null)
  const [cellSize, setCellSize] = useState(0)

  useLayoutEffect(() => {
    function measure() {
      if (!containerRef.current) return
      const w = containerRef.current.getBoundingClientRect().width
      setCellSize(w / gridN)
    }
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [gridN])

  // Lookup map for fast beam-path testing
  const beamSet = new Set()
  for (const p of beam.path) beamSet.add(`${p.row},${p.col}`)

  const hover = dragHandlers.hoverCell

  return (
    <div
      ref={containerRef}
      className="relative inline-grid border border-grid-line rounded-md bg-bg-lab shadow-[0_0_30px_rgba(0,245,255,0.08)]"
      style={{ gridTemplateColumns: `repeat(${gridN}, 1fr)`, touchAction: 'none' }}
    >
      {parsed.cells.map((row, r) =>
        row.map((cellData, c) => (
          <Cell
            key={`${r}-${c}`}
            row={r}
            col={c}
            cellData={cellData}
            playerMirror={playerCells[r][c]}
            isBeamPath={beamSet.has(`${r},${c}`)}
            isHovered={hover && hover.row === r && hover.col === c}
            inventoryRemaining={inventory}
            won={won}
            dragHandlers={dragHandlers}
            onRotate={onRotate}
            onRemove={onRemove}
          />
        ))
      )}
      <LightBeam
        path={beam.path}
        sourcePos={parsed.source}
        cellSize={cellSize}
        solved={beam.solved}
        gridN={gridN}
      />
    </div>
  )
}
