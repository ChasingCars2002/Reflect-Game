import { useCallback, useRef, useState } from 'react'

/**
 * Wraps HTML5 drag-and-drop into a small interface.
 * The drag payload is held in a ref because dragstart on inventory items
 * fires before React state propagates back to other elements.
 */
export function useDragDrop({ placeMirror, moveMirror, removeMirror }) {
  const dragRef = useRef(null)
  const [hoverCell, setHoverCell] = useState(null) // {row, col} | null

  const onDragStartInventory = useCallback((type, e) => {
    dragRef.current = { source: 'inventory', type }
    if (e?.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', `inv:${type}`)
    }
  }, [])

  const onDragStartCell = useCallback((row, col, type, e) => {
    dragRef.current = { source: 'cell', row, col, type }
    if (e?.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', `cell:${row},${col},${type}`)
    }
  }, [])

  const onDragOverCell = useCallback((row, col, e) => {
    e.preventDefault()
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
    if (!hoverCell || hoverCell.row !== row || hoverCell.col !== col) {
      setHoverCell({ row, col })
    }
  }, [hoverCell])

  const onDragLeaveCell = useCallback((row, col) => {
    setHoverCell((cur) => (cur && cur.row === row && cur.col === col ? null : cur))
  }, [])

  const onDropCell = useCallback(
    (row, col, e) => {
      e.preventDefault()
      const payload = dragRef.current
      setHoverCell(null)
      dragRef.current = null
      if (!payload) return
      if (payload.source === 'inventory') {
        placeMirror(row, col, payload.type)
      } else if (payload.source === 'cell') {
        moveMirror(payload.row, payload.col, row, col, payload.type)
      }
    },
    [placeMirror, moveMirror]
  )

  const onDragOverInventory = useCallback((e) => {
    if (dragRef.current?.source === 'cell') {
      e.preventDefault()
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
    }
  }, [])

  const onDropInventory = useCallback(
    (e) => {
      e.preventDefault()
      const payload = dragRef.current
      dragRef.current = null
      if (!payload || payload.source !== 'cell') return
      removeMirror(payload.row, payload.col)
    },
    [removeMirror]
  )

  const onDragEnd = useCallback(() => {
    dragRef.current = null
    setHoverCell(null)
  }, [])

  return {
    hoverCell,
    onDragStartInventory,
    onDragStartCell,
    onDragOverCell,
    onDragLeaveCell,
    onDropCell,
    onDragOverInventory,
    onDropInventory,
    onDragEnd,
  }
}
