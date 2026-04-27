import React from 'react'

const ARROW = { N: '▲', S: '▼', E: '▶', W: '◀' }

function MirrorGlyph({ variant, color }) {
  // 45° line drawn with a div + transform
  const rotation = variant === '/' ? '-rotate-45' : 'rotate-45'
  return (
    <div className="relative w-full h-full flex items-center justify-center pointer-events-none">
      <div
        className={`w-[78%] h-[3px] ${rotation} rounded-sm`}
        style={{
          background: color,
          boxShadow: `0 0 6px ${color}, 0 0 14px ${color}88`,
        }}
      />
    </div>
  )
}

export default function Cell({
  row,
  col,
  cellData,
  playerMirror,
  isBeamPath,
  isHovered,
  inventoryRemaining,
  won,
  dragHandlers,
  onRotate,
  onRemove,
}) {
  const baseClass =
    'relative w-16 h-16 sm:w-20 sm:h-20 border border-grid-line bg-cell-empty transition-colors duration-150'
  const beamClass = isBeamPath ? 'cell-beam-active' : ''
  const hoverClass = isHovered ? 'cell-drag-over' : ''

  const handleClick = () => {
    if (playerMirror !== null) onRotate(row, col)
  }

  const handleContextMenu = (e) => {
    e.preventDefault()
    if (playerMirror !== null) onRemove(row, col)
  }

  // Enable drop on empty cells (or cells with player mirror that we're moving to)
  const canDrop = cellData.type === 'empty' && playerMirror === null

  const dragProps = canDrop
    ? {
        onDragOver: (e) => dragHandlers.onDragOverCell(row, col, e),
        onDragLeave: () => dragHandlers.onDragLeaveCell(row, col),
        onDrop: (e) => dragHandlers.onDropCell(row, col, e),
      }
    : {}

  let content = null
  switch (cellData.type) {
    case 'source':
      content = (
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="w-10 h-10 sm:w-12 sm:h-12 rounded-md border border-neon-cyan flex items-center justify-center text-neon-cyan text-xl shadow-neon-cyan"
            style={{ background: 'rgba(0,245,255,0.08)' }}
          >
            <span>{ARROW[cellData.variant]}</span>
          </div>
        </div>
      )
      break
    case 'target': {
      const targetClasses = [
        'w-9 h-9 sm:w-11 sm:h-11 rounded-full border-2 border-neon-amber flex items-center justify-center',
        won ? 'animate-pulse-target' : 'shadow-neon-amber',
      ].join(' ')
      content = (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={targetClasses} style={{ background: 'rgba(255,179,0,0.08)' }}>
            <div className="w-3 h-3 rounded-full bg-neon-amber" />
          </div>
        </div>
      )
      break
    }
    case 'obstacle':
      content = (
        <div className="absolute inset-1 rounded-sm bg-[#1b1f2e] border border-[#2a3148]" />
      )
      break
    case 'fixed_mirror':
      content = (
        <div className="absolute inset-0">
          <MirrorGlyph variant={cellData.variant} color="#7e8aa3" />
        </div>
      )
      break
    case 'empty':
    default:
      if (playerMirror !== null) {
        const variant = playerMirror === 'M/' ? '/' : '\\'
        content = (
          <div
            className="absolute inset-0 cursor-pointer select-none"
            draggable
            onDragStart={(e) =>
              dragHandlers.onDragStartCell(row, col, variant, e)
            }
            onDragEnd={dragHandlers.onDragEnd}
            title="Click to rotate · Right-click to remove"
          >
            <MirrorGlyph variant={variant} color="#ff8c00" />
          </div>
        )
      }
      break
  }

  return (
    <div
      className={`${baseClass} ${beamClass} ${hoverClass}`}
      onClick={handleClick}
      onContextMenu={handleContextMenu}
      {...dragProps}
    >
      {content}
    </div>
  )
}
