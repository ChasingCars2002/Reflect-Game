import React, { useLayoutEffect, useRef, useState } from 'react'

/**
 * Renders the beam as an animated SVG polyline overlaying the grid.
 * The beam travels from the source cell through each path cell in order.
 *
 * Props:
 *   path: [{row, col, dir}]
 *   sourcePos: {row, col, dir}
 *   cellSize: pixels per cell
 *   solved: boolean (just for color tint potentially)
 */
export default function LightBeam({ path, sourcePos, cellSize, solved, gridN }) {
  const polyRef = useRef(null)
  const [length, setLength] = useState(0)
  const [animKey, setAnimKey] = useState(0)

  // Build polyline points: start at the center of the source cell, then go
  // through each path cell's center.
  let points = []
  if (sourcePos && cellSize > 0) {
    points.push([
      sourcePos.col * cellSize + cellSize / 2,
      sourcePos.row * cellSize + cellSize / 2,
    ])
    for (const p of path) {
      points.push([p.col * cellSize + cellSize / 2, p.row * cellSize + cellSize / 2])
    }
  }

  const pointsAttr = points.map(([x, y]) => `${x},${y}`).join(' ')

  useLayoutEffect(() => {
    if (polyRef.current && typeof polyRef.current.getTotalLength === 'function') {
      const len = polyRef.current.getTotalLength()
      setLength(len)
      setAnimKey((k) => k + 1)
    }
  }, [pointsAttr])

  if (points.length < 2 || cellSize <= 0) return null

  const totalSize = cellSize * gridN

  return (
    <svg
      className="absolute top-0 left-0 pointer-events-none"
      width={totalSize}
      height={totalSize}
      viewBox={`0 0 ${totalSize} ${totalSize}`}
    >
      <defs>
        <filter id="beam-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.4" result="blur1" />
          <feGaussianBlur in="SourceGraphic" stdDeviation="0.7" result="blur2" />
          <feMerge>
            <feMergeNode in="blur1" />
            <feMergeNode in="blur2" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <polyline
        key={animKey}
        ref={polyRef}
        points={pointsAttr}
        fill="none"
        stroke={solved ? '#00ffea' : '#00f5ff'}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#beam-glow)"
        style={{
          strokeDasharray: length || 1,
          strokeDashoffset: length || 1,
          animation:
            length > 0
              ? `beam-draw ${Math.max(300, Math.min(900, length * 1.5))}ms ease-out forwards`
              : 'none',
          ['--beam-length']: length,
        }}
      />
    </svg>
  )
}
