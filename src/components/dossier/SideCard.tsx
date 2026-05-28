interface FactRow {
  label: string
  value: string
}

interface Props {
  title: string
  facts?: FactRow[]
  children?: React.ReactNode
}

export default function SideCard({ title, facts, children }: Props) {
  return (
    <div className="side-card">
      <div className="side-card-head">{title}</div>
      {facts && (
        <div className="flex flex-col">
          {facts.map((f, i) => (
            <div
              key={i}
              className="flex items-baseline justify-between py-2.5"
              style={{ borderBottom: '1px dashed var(--rule-soft)' }}
            >
              <span
                className="text-[13px]"
                style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }}
              >
                {f.label}
              </span>
              <span
                className="text-[13px] font-semibold ml-3 text-right"
                style={{
                  color: 'var(--ink)',
                  fontFamily: 'var(--font-sans)',
                  fontVariantNumeric: 'tabular-nums lining-nums',
                }}
              >
                {f.value}
              </span>
            </div>
          ))}
        </div>
      )}
      {children}
    </div>
  )
}
