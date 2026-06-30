import { useState, useEffect } from 'react'
import { loadResearchSnapshot } from '../data/researchSnapshot'
import RelatedPages from './RelatedPages'
import ResearchOverview from './research/ResearchOverview'
import ResearchAbout from './research/ResearchAbout'
import ResearchProblem from './research/ResearchProblem'
import ResearchMethodology from './research/ResearchMethodology'

import ResearchFinancialArchetypes from './research/ResearchFinancialArchetypes'
import ResearchEntityTypes from './research/ResearchEntityTypes'

import ResearchFindings from './research/ResearchFindings'
import ResearchSpending from './research/ResearchSpending'
import ResearchDataMovement from './research/ResearchDataMovement'

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

    { id: 'financial-archetypes', component: ResearchFinancialArchetypes },
    { id: 'entity-types', component: ResearchEntityTypes },

    { id: 'findings', component: ResearchFindings },
    { id: 'spending', component: ResearchSpending },
    { id: 'data-movement', component: ResearchDataMovement },
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
        <footer className="mt-20 pt-8 border-t border-cool-grey/20">
          <div className="text-xs text-cool-grey mb-6">
            <p className="mb-2">
              Data current as of: {new Date(metadata.data_period).toLocaleDateString()}
            </p>
            <p>
              Total organizations indexed: {metadata.total_organizations?.toLocaleString()}
            </p>
            <p className="mt-4">{metadata.disclaimer}</p>
          </div>
          <RelatedPages
            links={[
              { to: '/methodology', label: 'How we score' },
              { to: '/about', label: 'About Daanaa' },
              { to: '/principles', label: 'Our principles' },
            ]}
          />
          <div className="mt-12 pt-6 border-t border-cool-grey/20 flex items-center justify-between">
            <a
              href="/"
              className="text-soft-gold hover:text-bright-gold font-semibold text-sm transition-colors"
            >
              ← Back to Daanaa
            </a>
            <span className="text-xs text-cool-grey">Research Dashboard</span>
          </div>
        </footer>
      )}
    </div>
  )
}
