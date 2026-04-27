import React from 'react'

function MirrorIcon({ variant }) {
  const rotation = variant === '/' ? '-rotate-45' : 'rotate-45'
  return (
    <div className="relative w-full h-full flex items-center justify-center pointer-events-none">
      <div
        className={`w-[78%] h-[3px] ${rotation} rounded-sm`}
        style={{
          background: '#ff8c00',
          boxShadow: '0 0 6px #ff8c00, 0 0 14px rgba(255,140,0,0.5)',
        }}
      />
    </div>
  )
}

export default function MirrorInventory({ count, total, dragHandlers }) {
  const slots = Array.from({ length: total })
  return (
    <div
      className="mt-6 p-4 bg-cell-empty border border-grid-line rounded-lg flex items-center gap-4 min-w-[320px]"
      onDragOver={dragHandlers.onDragOverInventory}
      onDrop={dragHandlers.onDropInventory}
    >
      <div className="text-cyan-300 text-xs uppercase tracking-widest opacity-80">
        Mirrors&nbsp;
        <span className="text-neon-cyan font-bold">
          {count}
          <span className="opacity-50">/{total}</span>
        </span>
      </div>
      <div className="flex gap-3">
        {slots.map((_, i) => {
          const available = i < count
          return (
            <div
              key={i}
              className={`w-12 h-12 border rounded-md flex items-center justify-center transition-opacity ${
                available
                  ? 'border-neon-orange cursor-grab active:cursor-grabbing shadow-neon-orange'
                  : 'border-[#2a3148] opacity-25'
              }`}
              draggable={available}
              onDragStart={
                available
                  ? (e) => dragHandlers.onDragStartInventory('\\', e)
                  : undefined
              }
              onDragEnd={dragHandlers.onDragEnd}
              title={
                available
                  ? 'Drag to grid · Click placed mirror to rotate'
                  : 'Mirror in use'
              }
            >
              {available ? <MirrorIcon variant="\\" /> : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}
