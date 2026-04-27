import React from 'react'

function DifficultyDots({ value }) {
  const dots = [1, 2, 3, 4]
  return (
    <span className="inline-flex gap-1 ml-2">
      {dots.map((d) => (
        <span
          key={d}
          className={`inline-block w-2 h-2 rounded-full ${
            d <= value ? 'bg-neon-amber shadow-neon-amber' : 'bg-[#2a3148]'
          }`}
        />
      ))}
    </span>
  )
}

function Btn({ children, disabled, onClick, primary }) {
  const base =
    'px-3 py-1.5 text-xs uppercase tracking-widest border rounded transition-colors'
  const cls = primary
    ? `${base} border-neon-cyan text-neon-cyan hover:bg-neon-cyan hover:text-bg-lab`
    : `${base} border-grid-line text-cyan-300 hover:border-neon-cyan hover:text-neon-cyan`
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`${cls} ${disabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      {children}
    </button>
  )
}

export default function HUD({
  level,
  levelIndex,
  totalLevels,
  won,
  onPrev,
  onNext,
  onReset,
}) {
  return (
    <div className="w-full max-w-[640px] mb-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="text-neon-cyan text-2xl font-mono tracking-wider text-shadow-cyan">
          REFLECT
        </span>
        <span className="text-cyan-200 opacity-70 text-sm">
          {level.title || `Level ${level.id}`}
          <span className="opacity-50">
            {' '}
            ({levelIndex + 1}/{totalLevels})
          </span>
        </span>
        <DifficultyDots value={level.difficulty || 1} />
      </div>
      <div className="flex items-center gap-2">
        <Btn disabled={levelIndex === 0} onClick={onPrev}>
          ◀ Prev
        </Btn>
        <Btn onClick={onReset}>Reset</Btn>
        <Btn
          primary
          disabled={levelIndex === totalLevels - 1}
          onClick={onNext}
        >
          Next ▶
        </Btn>
      </div>
    </div>
  )
}

export function WinOverlay({ visible, onNext, isLast }) {
  if (!visible) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="text-center">
        <div className="text-neon-cyan text-5xl font-mono tracking-[0.3em] animate-win-glow">
          BEAM CONNECTED
        </div>
        <div className="mt-3 text-cyan-200 opacity-80 text-sm tracking-widest">
          Target acquired
        </div>
        <button
          onClick={onNext}
          disabled={isLast}
          className={`mt-8 px-6 py-2 border-2 border-neon-cyan text-neon-cyan text-sm uppercase tracking-widest rounded transition-colors ${
            isLast
              ? 'opacity-40 cursor-not-allowed'
              : 'hover:bg-neon-cyan hover:text-bg-lab cursor-pointer'
          }`}
        >
          {isLast ? 'All levels complete' : 'Next level →'}
        </button>
      </div>
    </div>
  )
}
