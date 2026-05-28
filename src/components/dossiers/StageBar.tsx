interface Props {
  stage: number // 1–5
}

const STAGE_LABELS = ['Dossier', 'Marché', 'Analyse', 'Synthèse', 'Rapport']

export default function StageBar({ stage }: Props) {
  return (
    <div
      className="flex gap-0.5"
      role="progressbar"
      aria-valuenow={stage}
      aria-valuemin={1}
      aria-valuemax={5}
      aria-label={`Étape ${stage} sur 5`}
    >
      {STAGE_LABELS.map((label, i) => (
        <div
          key={label}
          title={label}
          className="h-[3px] flex-1 rounded-[2px] transition-colors"
          style={{
            background:
              i + 1 < stage
                ? 'var(--navy)'
                : i + 1 === stage
                ? 'var(--ochre)'
                : 'var(--rule)',
          }}
        />
      ))}
    </div>
  )
}
