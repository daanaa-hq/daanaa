import { useState, useEffect } from 'react'
import ResearchOverview from './research/ResearchOverview'
import ResearchAbout from './research/ResearchAbout'
import ResearchProblem from './research/ResearchProblem'
import ResearchMethodology from './research/ResearchMethodology'
import ResearchOperatingModels from './research/ResearchOperatingModels'
import ResearchRevenueMatrix from './research/ResearchRevenueMatrix'
import ResearchPeerContext from './research/ResearchPeerContext'
import ResearchLampTiers from './research/ResearchLampTiers'
import ResearchCoverage from './research/ResearchCoverage'
import ResearchFindings from './research/ResearchFindings'
import ResearchSpending from './research/ResearchSpending'

interface ResearchContentProps {
  sessionToken: string
}

export default function ResearchContent({ sessionToken }: ResearchContentProps) {
  const [metadata, setMetadata] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const response = await fetch('/api/research/metadata', {
          headers: { 'X-Research-Session': sessionToken },
        })
        if (response.ok) {
          const data = await response.json()
          setMetadata(data)
        }
      } catch (error) {
        console.error('Failed to load research metadata:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchMetadata()
  }, [sessionToken])

  const sections = [
    { id: 'overview', component: ResearchOverview },
    { id: 'about', component: ResearchAbout },
    { id: 'problem', component: ResearchProblem },
    { id: 'methodology', component: ResearchMethodology },
    { id: 'operating-models', component: ResearchOperatingModels },
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
            Data current as of: {new Date(metadata.last_updated).toLocaleDateString()}
          </p>
          <p>
            Total organizations indexed: {metadata.total_orgs?.toLocaleString()}
          </p>
          <p className="mt-4 text-cool-grey/60">{metadata.disclaimer}</p>
        </footer>
      )}
    </div>
  )
}
