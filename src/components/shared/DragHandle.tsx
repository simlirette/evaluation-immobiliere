'use client'

interface Props {
  onDrag: (delta: number) => void
  onDragEnd?: () => void
}

export default function DragHandle({ onDrag, onDragEnd }: Props) {
  function handleMouseDown(e: React.MouseEvent) {
    e.preventDefault()

    function handleMouseMove(me: MouseEvent) {
      onDrag(me.movementX)
    }

    function handleMouseUp() {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      onDragEnd?.()
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  return (
    <div
      onMouseDown={handleMouseDown}
      className="flex-shrink-0 w-2 cursor-col-resize relative group select-none"
      title="Glisser pour redimensionner"
      role="separator"
      aria-orientation="vertical"
    >
      <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-[3px] rounded-full bg-transparent group-hover:bg-black/[.10] transition-colors duration-150" />
    </div>
  )
}
