import React, { useCallback, useState } from 'react'
import { levels } from './data/levels'
import { useGameState } from './hooks/useGameState'
import { useDragDrop } from './hooks/useDragDrop'
import GameBoard from './components/GameBoard'
import MirrorInventory from './components/MirrorInventory'
import HUD, { WinOverlay } from './components/HUD'

export default function App() {
  const [levelIndex, setLevelIndex] = useState(0)
  const level = levels[levelIndex]

  const game = useGameState(level)

  const dragHandlers = useDragDrop({
    placeMirror: game.placeMirror,
    moveMirror: game.moveMirror,
    removeMirror: game.removeMirror,
  })

  const goPrev = useCallback(() => {
    setLevelIndex((i) => Math.max(0, i - 1))
  }, [])
  const goNext = useCallback(() => {
    setLevelIndex((i) => Math.min(levels.length - 1, i + 1))
  }, [])

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-start p-6 bg-bg-lab">
      <div className="w-full max-w-[720px] flex flex-col items-center">
        <HUD
          level={level}
          levelIndex={levelIndex}
          totalLevels={levels.length}
          won={game.won}
          onPrev={goPrev}
          onNext={goNext}
          onReset={game.resetLevel}
        />

        <GameBoard
          parsed={game.parsed}
          playerCells={game.playerCells}
          beam={game.beam}
          inventory={game.inventory}
          won={game.won}
          dragHandlers={dragHandlers}
          onRotate={game.rotateMirror}
          onRemove={game.removeMirror}
        />

        <MirrorInventory
          count={game.inventory}
          total={game.initialInventory}
          dragHandlers={dragHandlers}
        />

        <div className="mt-6 text-cyan-300 opacity-60 text-xs max-w-md text-center leading-relaxed">
          <p>
            Drag mirrors onto empty cells. Click a placed mirror to rotate it
            (<span className="text-neon-orange">/</span> ↔{' '}
            <span className="text-neon-orange">\</span>). Right-click or drag
            back to inventory to remove. Bounce the beam from{' '}
            <span className="text-neon-cyan">▶</span> to{' '}
            <span className="text-neon-amber">◎</span>.
          </p>
        </div>
      </div>

      <WinOverlay
        visible={game.won}
        onNext={goNext}
        isLast={levelIndex === levels.length - 1}
      />
    </div>
  )
}
