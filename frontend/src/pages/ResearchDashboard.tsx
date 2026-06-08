import { useState, useEffect, useRef } from 'react'
import ResearchAccess from '../components/ResearchAccess'
import ResearchSidebar from '../components/ResearchSidebar'
import ResearchContent from '../components/ResearchContent'

export default function ResearchDashboard() {
  const [sessionToken, setSessionToken] = useState<string | null>(null)
  const [currentSection, setCurrentSection] = useState('overview')
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const stored = localStorage.getItem('research_session_token')
    const expiry = localStorage.getItem('research_session_expiry')

    if (stored && expiry) {
      const expiryTime = parseInt(expiry, 10)
      if (Date.now() < expiryTime) {
        setSessionToken(stored)
        return
      }
    }

    localStorage.removeItem('research_session_token')
    localStorage.removeItem('research_session_expiry')
  }, [])

  const handleSessionStart = (token: string) => {
    setSessionToken(token)
  }

  const handleSectionChange = (sectionId: string) => {
    setCurrentSection(sectionId)
    const element = document.getElementById(`section-${sectionId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  if (!sessionToken) {
    return <ResearchAccess onSuccess={handleSessionStart} />
  }

  return (
    <div className="flex h-screen bg-warm-cream">
      <ResearchSidebar
        currentSection={currentSection}
        onSectionChange={handleSectionChange}
      />
      <div
        ref={contentRef}
        className="flex-1 overflow-y-auto"
        onScroll={(e) => {
          const element = e.target as HTMLDivElement
          const sections = document.querySelectorAll('[data-section]')

          sections.forEach((section) => {
            const rect = section.getBoundingClientRect()
            if (rect.top >= 0 && rect.top < window.innerHeight / 2) {
              setCurrentSection(section.getAttribute('data-section') || '')
            }
          })
        }}
      >
        <ResearchContent sessionToken={sessionToken} />
      </div>
    </div>
  )
}
