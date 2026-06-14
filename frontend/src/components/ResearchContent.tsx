import { useState, useEffect } from 'react'
import { loadResearchSnapshot } from '../data/researchSnapshot'
import ResearchOverview from './research/ResearchOverview'
import ResearchAbout from './research/ResearchAbout'
import ResearchProblem from './research/ResearchProblem'
import ResearchMethodology from './research/ResearchMethodology'
import ResearchOperatingModels from './research/ResearchOperatingModels'
import ResearchFinancialArchetypes from './research/ResearchFinancialArchetypes'
import ResearchEntityTypes from './research/ResearchEntityTypes'
import ResearchPeerContext from './research/ResearchPeerContext'
import ResearchFindings from './research/ResearchFindings'
import ResearchSpending from './research/ResearchSpending'

interface ResearchContentProps {
  sessionToken: string
}

export default function ResearchContent({ sessionToken }: ResearchContentProps) {
  const [metadata, setMetadata] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResearchSnapshot()
      .then((snap) => setMetadata(snap.metadata))
      .catch((error) => console.error('Failed to load research snapshot:', error))
      .finally(() => setLoading(false))
  }, [])

  const sections = [
    { id: 'overview', component: ResearchOverview },
    { id: 'about', component: ResearchAbout },
    { id: 'problem', component: ResearchProblem },
    { id: 'methodology', component: ResearchMethodology },
    { id: 'operating-models', component: ResearchOperatingModels },
    { id: 'financial-archetypes', component: ResearchFinancialArchetypes },
    { id: 'entity-types', component: ResearchEntityTypes },
    { id: 'peer-context', component: ResearchPeerContext },
    { id: 'findings', component: ResearchFindings },
    { id: 'spending', component: ResearchSpending },
  ]

  return (
    <div className="max-w-5xl mx-auto p-8">
      {sections.map(({ id, component: Component }) => (
        <section
          key={id}
          id={`section-${id}`}
          data-section={id}
          className="mb-16 scroll-mt-20"
        >
          <Component sessionToken={sessionToken} metadata={metadata} />
        </section>
      ))}

      {metadata && (
        <footer className="mt-20 pt-8 border-t border-cool-grey/20 text-xs text-cool-grey">
          <p className="mb-2">
            Data current as of: {new Date(metadata.data_period).toLocaleDateString()}
          </p>
          <p>
            Total organizations indexed: {metadata.total_organizations?.toLocaleString()}
          </p>
          <p className="mt-4 text-cool-grey">{metadata.disclaimer}</p>
        </footer>
      )}
    </div>
  )
}
