'use client'

import { useEffect, useState, useCallback } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Table } from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import { marked } from 'marked'
import TurndownService from 'turndown'
import { gfm } from 'turndown-plugin-gfm'
import { exportRapport } from '@/lib/runtime-api'
import { printWindow } from '@/lib/print-window'

const td = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  bulletListMarker: '-',
})
td.use(gfm)

interface Props {
  initialMarkdown: string
  sessionId: string
  dossierId: string
  address?: string
  onSave: (markdown: string) => Promise<void>
  onGenerate: (format: 'abrege' | 'complet') => Promise<void>
  onSaveVersion: (markdown: string) => Promise<void>
}

function ToolbarButton({
  onClick,
  active,
  title,
  children,
}: {
  onClick: () => void
  active: boolean
  title: string
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`w-7 h-7 rounded-[6px] text-[12px] flex items-center justify-center transition-colors ${
        active
          ? 'bg-[#1a1916] text-white'
          : 'text-[#5a5854] hover:bg-black/[.06]'
      }`}
    >
      {children}
    </button>
  )
}

export default function RapportEditor({ initialMarkdown, sessionId, dossierId, address, onSave, onGenerate, onSaveVersion }: Props) {
  const [isEdited, setIsEdited] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [toast, setToast] = useState('')

  const editor = useEditor({
    extensions: [
      StarterKit,
      Table.configure({ resizable: false }),
      TableRow,
      TableCell,
      TableHeader,
    ],
    content: '',
    onUpdate: () => setIsEdited(true),
    editorProps: {
      attributes: {
        class: 'focus:outline-none min-h-[200px]',
      },
    },
  })

  useEffect(() => {
    if (!editor || !initialMarkdown) return
    const html = String(marked.parse(initialMarkdown))
    editor.commands.setContent(html, { emitUpdate: false })
    setIsEdited(false)
  }, [editor, initialMarkdown])

  const handleSave = useCallback(async () => {
    if (!editor || isSaving) return
    setIsSaving(true)
    try {
      const markdown = td.turndown(editor.getHTML())
      await onSave(markdown)
      setIsEdited(false)
      setToast('Rapport sauvegardé')
      setTimeout(() => setToast(''), 2000)
    } finally {
      setIsSaving(false)
    }
  }, [editor, isSaving, onSave])

  const handleGenerate = useCallback(
    async (format: 'abrege' | 'complet') => {
      const label = format === 'complet' ? 'forme complète (15 sections)' : 'forme abrégée'
      if (!confirm(`La régénération remplacera le contenu actuel (${label}). Continuer ?`)) return
      setIsGenerating(true)
      try {
        await onGenerate(format)
        setIsEdited(false)
      } finally {
        setIsGenerating(false)
      }
    },
    [onGenerate]
  )

  const handleExport = useCallback(
    async (format: 'docx' | 'html') => {
      if (isExporting) return
      setIsExporting(true)
      try {
        const { filename, blob } = await exportRapport(sessionId, format)
        if (format === 'docx') {
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = filename
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
        } else {
          const url = URL.createObjectURL(blob)
          window.open(url, '_blank')
          setTimeout(() => URL.revokeObjectURL(url), 10_000)
        }
      } finally {
        setIsExporting(false)
      }
    },
    [isExporting, sessionId]
  )

  const handleSaveVersion = useCallback(async () => {
    if (!editor) return
    const markdown = td.turndown(editor.getHTML())
    await onSaveVersion(markdown)
  }, [editor, onSaveVersion])

  if (!editor) return null

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Toolbar */}
      <div
        className="flex items-center gap-1 px-3 py-2 border-b border-black/[.06] flex-shrink-0"
        style={{ background: 'rgba(255,255,255,.70)' }}
      >
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive('bold')}
          title="Gras"
        >
          <strong>B</strong>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive('italic')}
          title="Italique"
        >
          <em>I</em>
        </ToolbarButton>
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          active={editor.isActive('heading', { level: 2 })}
          title="Titre 2"
        >
          H2
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          active={editor.isActive('heading', { level: 3 })}
          title="Titre 3"
        >
          H3
        </ToolbarButton>
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive('bulletList')}
          title="Liste à puces"
        >
          ≡
        </ToolbarButton>
        <div className="flex-1" />
        {toast && (
          <span className="text-[11px] text-emerald-600 mr-2 transition-opacity">{toast}</span>
        )}
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <button
          type="button"
          onClick={() => handleExport('docx')}
          disabled={isExporting}
          title="Télécharger .docx"
          className="rounded-full px-2.5 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] disabled:opacity-40 transition-colors"
        >
          {isExporting ? '…' : '⬇ .docx'}
        </button>
        <button
          type="button"
          onClick={() => printWindow(editor.getHTML(), address ?? 'Rapport évaluation')}
          title="Aperçu PDF (imprimer depuis le navigateur)"
          className="rounded-full px-2.5 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
        >
          🖨 PDF
        </button>
        <button
          type="button"
          onClick={handleSaveVersion}
          title="Sauvegarder comme nouvelle version"
          className="rounded-full px-2.5 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
        >
          📌 Sauv. version
        </button>
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <button
          type="button"
          onClick={handleSave}
          disabled={!isEdited || isSaving}
          className="rounded-full px-3 py-1.5 text-[12px] bg-[#334155] text-white disabled:opacity-40 transition-opacity"
        >
          {isSaving ? 'Sauvegarde...' : 'Sauvegarder ✓'}
        </button>
      </div>

      {/* Editor content */}
      <div className="flex-1 overflow-y-auto px-8 py-5 scroll-fade">
        <div className="text-[13px] leading-[1.75] text-[#1a1916] [&_h1]:text-[18px] [&_h1]:font-semibold [&_h1]:mb-2 [&_h2]:text-[15px] [&_h2]:font-semibold [&_h2]:mt-5 [&_h2]:mb-1.5 [&_h3]:text-[13px] [&_h3]:font-medium [&_h3]:mt-3 [&_h3]:mb-1 [&_table]:w-full [&_table]:text-[12px] [&_table]:border-collapse [&_th]:text-left [&_th]:px-2 [&_th]:py-1.5 [&_th]:font-medium [&_th]:bg-black/[.025] [&_td]:px-2 [&_td]:py-1.5 [&_td]:border-t [&_td]:border-black/[.05] [&_blockquote]:border-l-2 [&_blockquote]:border-amber-400 [&_blockquote]:pl-3 [&_blockquote]:text-[12px] [&_blockquote]:text-amber-800 [&_blockquote]:bg-amber-50/60 [&_blockquote]:rounded-r-[4px] [&_blockquote]:py-1">
          <EditorContent editor={editor} />
        </div>
      </div>

      {/* Footer */}
      <div
        className="flex items-center gap-2 px-4 py-2.5 border-t border-black/[.06] flex-shrink-0"
        style={{ background: 'rgba(255,255,255,.60)' }}
      >
        <span className="text-[11px] text-[#b5b2ac] mr-1">Régénérer :</span>
        <button
          type="button"
          onClick={() => handleGenerate('abrege')}
          disabled={isGenerating}
          className="rounded-full px-3 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] disabled:opacity-40 transition-colors"
        >
          {isGenerating ? 'Génération...' : 'Forme abrégée'}
        </button>
        <button
          type="button"
          onClick={() => handleGenerate('complet')}
          disabled={isGenerating}
          className="rounded-full px-3 py-1.5 text-[11px] bg-[#1f7a5c]/10 text-[#1f7a5c] border border-[#1f7a5c]/20 hover:bg-[#1f7a5c]/20 disabled:opacity-40 transition-colors"
        >
          {isGenerating ? 'Génération...' : 'Forme complète →'}
        </button>
      </div>
    </div>
  )
}
