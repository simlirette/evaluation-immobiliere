import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import AdjustmentsTable from '@/components/shared/AdjustmentsTable'
import ValeurCard from '@/components/shared/ValeurCard'
import ChatInput from '@/components/shared/ChatInput'
import { MOCK_ADJUSTMENTS } from '@/data/mock'

export default function AnalysePanel() {
  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Applique un ajustement +5% pour la rénovation 2019 et tiens compte du garage double</UserMessage>
        <AgentMessage agentName="Agent Analyse">
          Voici le tableau d'ajustements :
          <AdjustmentsTable rows={MOCK_ADJUSTMENTS} />
          <ValeurCard
            range="1 265 000 $ – 1 320 000 $"
            median="Médiane ajustée : 1 289 500 $"
          />
        </AgentMessage>
        <AgentMessage agentName="Agent Analyse" last>
          Fourchette retenue : <strong>1 265 000 $ à 1 320 000 $</strong>.
        </AgentMessage>
      </div>
      <ChatInput placeholder="Modifier les ajustements..." />
    </div>
  )
}
