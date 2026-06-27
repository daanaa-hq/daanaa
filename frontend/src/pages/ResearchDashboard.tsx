import { useState, useEffect } from 'react'
import ResearchSidebar from '../components/ResearchSidebar'
import ResearchContent from '../components/ResearchContent'

// Public dashboard — aggregate IRS data served from a static snapshot. The
// passcode gate was removed 2026-06-09 (audit Session 2): nothing private here.
export default function ResearchDashboard() {
  const [currentSection, setCurrentSection] = useState('overview')

  const handleSectionChange = (sectionId: string) => {
    setCurrentSection(sectionId)
    const element = document.getElementById(`section-${sectionId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  // Track active section via IntersectionObserver on the page scroll (not inner div)
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setCurrentSection(entry.target.getAttribute('data-section') || '')
          }
        }
      },
      { rootMargin: '-40% 0px -55% 0px' }
    )
    document.querySelectorAll('[data-section]').forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <div className="flex min-h-screen bg-warm-cream">
      <ResearchSidebar
        currentSection={currentSection}
        onSectionChange={handleSectionChange}
      />
      <div className="flex-1 min-w-0">
        <ResearchContent sessionToken="" />
      </div>
    </div>
  )
}
