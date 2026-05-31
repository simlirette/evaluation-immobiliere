'use client'

import { useState } from 'react'
import { saveRuntimeSignature, generateCertifiedExport, type SignatureData } from '@/lib/runtime-api'

interface Props {
  dossierId: string
  initial?: SignatureData | null
  onSigned?: (signature: SignatureData) => void
}

export default function SignatureForm({ dossierId, initial, onSigned }: Props) {
  const [nomEa, setNomEa] = useState(initial?.nom_ea ?? '')
  const [noPermis, setNoPermis] = useState(initial?.no_permis_oeaq ?? '')
  const [dateSig, setDateSig] = useState(
    initial?.date_signature ?? new Date().toISOString().slice(0, 10)
  )
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [signed, setSigned] = useState(!!initial?.signe_le)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [htmlContent, setHtmlContent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const canSign = nomEa.trim().length > 0 && noPermis.trim().length > 0 && dateSig.length > 0

  async function handleSign() {
    if (!canSign) return
    setSaving(true)
    setError(null)
    try {
      const result = await saveRuntimeSignature(dossierId, {
        nom_ea: nomEa.trim(),
        no_permis_oeaq: noPermis.trim(),
        date_signature: dateSig,
      })
      setSigned(true)
      onSigned?.(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  async function handleExport() {
    setGenerating(true)
    setError(null)
    try {
      const result = await generateCertifiedExport(dossierId)
      setHtmlContent(result.html_certified)
      if (result.pdf_b64) {
        const blob = new Blob(
          [Uint8Array.from(atob(result.pdf_b64), c => c.charCodeAt(0))],
          { type: 'application/pdf' }
        )
        setPdfUrl(URL.createObjectURL(blob))
      }
      if (result.pdf_error) {
        setError(`PDF non généré : ${result.pdf_error}`)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setGenerating(false)
    }
  }

  function handleDownloadHtml() {
    if (!htmlContent) return
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rapport-certifie-${dossierId}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-col gap-3 p-4 rounded-[10px]"
      style={{ border: '1px solid rgba(74,107,84,.3)', background: 'rgba(74,107,84,.03)' }}>

      <div className="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden
          className="flex-shrink-0" style={{ color: 'var(--verdigris)' }}>
          <path d="M2 7l3.5 3.5L12 3" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span className="text-[11px] uppercase tracking-widest" style={{ color: 'var(--verdigris)' }}>
          Signature É.A. — Export certifié
        </span>
      </div>

      {!signed ? (
        <>
          <p className="text-[12px]" style={{ color: 'var(--ink-mute)' }}>
            En signant, vous attestez avoir révisé le rapport et vous engagez en tant qu'évaluateur agréé
            membre de l'OEAQ. Cette action est horodatée et ne peut être annulée.
          </p>

          <div className="flex flex-col gap-1">
            <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>Nom complet É.A. *</label>
            <input
              type="text"
              value={nomEa}
              onChange={e => setNomEa(e.target.value)}
              placeholder="Prénom Nom"
              className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
              style={{ border: '1px solid var(--rule)', background: 'var(--paper)', color: 'var(--ink)' }}
            />
          </div>

          <div className="flex gap-2">
            <div className="flex flex-col gap-1 flex-1">
              <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>N° permis OEAQ *</label>
              <input
                type="text"
                value={noPermis}
                onChange={e => setNoPermis(e.target.value)}
                placeholder="ex. 4321"
                className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
                style={{ border: '1px solid var(--rule)', background: 'var(--paper)', color: 'var(--ink)' }}
              />
            </div>
            <div className="flex flex-col gap-1 flex-1">
              <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>Date de signature *</label>
              <input
                type="date"
                value={dateSig}
                onChange={e => setDateSig(e.target.value)}
                className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
                style={{ border: '1px solid var(--rule)', background: 'var(--paper)', color: 'var(--ink)' }}
              />
            </div>
          </div>

          {error && <p className="text-[12px]" style={{ color: 'var(--oxblood)' }}>{error}</p>}

          <button
            onClick={handleSign}
            disabled={!canSign || saving}
            className="btn accent disabled:opacity-40 text-[12px] py-1.5"
          >
            {saving ? 'Enregistrement…' : 'Signer le rapport'}
          </button>
        </>
      ) : (
        <>
          <div className="flex items-center gap-2 px-3 py-2 rounded-[8px]"
            style={{ background: 'rgba(74,107,84,.08)', border: '1px solid rgba(74,107,84,.2)' }}>
            <span className="text-[12px] font-semibold" style={{ color: 'var(--verdigris)' }}>
              ✓ Signé — {nomEa || initial?.nom_ea} | Permis {noPermis || initial?.no_permis_oeaq}
            </span>
          </div>

          {!htmlContent && (
            <button
              onClick={handleExport}
              disabled={generating}
              className="btn accent disabled:opacity-40 text-[12px] py-1.5"
            >
              {generating ? 'Génération…' : 'Générer rapport certifié (HTML + PDF)'}
            </button>
          )}

          {error && <p className="text-[12px]" style={{ color: 'var(--oxblood)' }}>{error}</p>}

          {htmlContent && (
            <div className="flex gap-2">
              <button
                onClick={handleDownloadHtml}
                className="btn text-[12px] py-1.5 flex-1"
                style={{ border: '1px solid var(--rule)', background: 'var(--paper-hi)' }}
              >
                ↓ HTML certifié
              </button>
              {pdfUrl && (
                <a
                  href={pdfUrl}
                  download={`rapport-certifie-${dossierId}.pdf`}
                  className="btn accent text-[12px] py-1.5 flex-1 text-center no-underline"
                >
                  ↓ PDF certifié
                </a>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
