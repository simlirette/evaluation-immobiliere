'use client'

import { useState, useRef } from 'react'

interface Props {
  onDrop: (files: FileList) => void
}

export default function DropZone({ onDrop }: Props) {
  const [over, setOver] = useState(false)
  const counter = useRef(0)

  return (
    <div className="flex-1 flex flex-col items-center justify-center mb-6">
      <div
        className={`w-full max-w-[460px] text-center rounded-[22px] py-[52px] px-8 transition-[border-color,background] duration-150 border-[1.5px] border-dashed ${
          over ? 'border-[#334155] bg-[rgba(51,65,85,.04)]' : 'border-black/[.15]'
        }`}
        onDragEnter={e => { e.preventDefault(); counter.current++; setOver(true) }}
        onDragLeave={() => { if (--counter.current <= 0) { counter.current = 0; setOver(false) } }}
        onDragOver={e => e.preventDefault()}
        onDrop={e => { e.preventDefault(); counter.current = 0; setOver(false); onDrop(e.dataTransfer.files) }}
      >
        <div className="w-[52px] h-[52px] rounded-[16px] bg-[rgba(51,65,85,.08)] mx-auto mb-[18px] flex items-center justify-center">
          <svg width="24" height="24" fill="none" stroke="#334155" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
          </svg>
        </div>
        <div className="text-[20px] font-medium text-[#1a1916] mb-1.5 tracking-[.01em]"
          style={{ fontFamily: 'var(--font-serif)' }}>
          Déposez les documents du dossier
        </div>
        <div className="text-[13px] text-[#8a8780] font-light leading-relaxed">
          Certificat de localisation, titre de propriété,<br/>photos, plans — PDF, JPG, PNG
        </div>
        <div className="text-[11px] text-[#b5b2ac] my-4 uppercase tracking-[.06em]">ou</div>
        <button className="px-[22px] py-2 bg-[#334155] text-white border-none rounded-full text-[13px] cursor-pointer hover:opacity-85 transition-opacity">
          Parcourir les fichiers
        </button>
      </div>
    </div>
  )
}
