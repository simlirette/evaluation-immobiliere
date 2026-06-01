'use client'

/** Indicateur de loading agent — 3 dots qui rebondissent en séquence (style Claude) */
export default function TypingDots() {
  return (
    <span className="inline-flex items-end gap-[3px] h-4" aria-label="En cours de rédaction…">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-[5px] h-[5px] rounded-full bg-[#b5b2ac]"
          style={{
            animation: 'typing-bounce 1.2s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
      <style>{`
        @keyframes typing-bounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
          30% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </span>
  )
}
