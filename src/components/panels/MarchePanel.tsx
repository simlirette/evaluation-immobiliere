import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import ComparableItem from '@/components/shared/ComparableItem'
import ChatInput from '@/components/shared/ChatInput'
import { MOCK_COMPARABLES } from '@/data/mock'

export default function MarchePanel() {
  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Unifamiliales R-2, rayon 1 km, vendues dans les 18 derniers mois</UserMessage>
        <AgentMessage agentName="Agent Marché">
          J'ai identifié <strong>4 comparables</strong> correspondant aux critères.
          <div className="flex flex-col gap-2 mt-2.5">
            {MOCK_COMPARABLES.map((c, i) => <ComparableItem key={i} comp={c} />)}
          </div>
        </AgentMessage>
        <AgentMessage agentName="Agent Marché" last>
          Prix médian des comparables : <strong>1 252 500 $</strong>. Fourchette : 1 150 000 $ – 1 420 000 $.
        </AgentMessage>
      </div>
      <ChatInput placeholder="Affiner les critères de recherche..." />
    </div>
  )
}
