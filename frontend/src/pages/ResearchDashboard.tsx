import { useState, useRef } from 'react'
import ResearchSidebar from '../components/ResearchSidebar'
import ResearchContent from '../components/ResearchContent'
import Footer from '../components/Footer'

// Public dashboard — aggregate IRS data served from a static snapshot. The
// passcode gate was removed 2026-06-09 (audit Session 2): nothing private here.
export default function ResearchDashboard() {
  const [currentSection, setCurrentSection] = useState('overview')
  const contentRef = useRef<HTMLDivElement>(null)

  const handleSectionChange = (sectionId: string) => {
    setCurrentSection(sectionId)
    const element = document.getElementById(`section-${sectionId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
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
        <ResearchContent sessionToken="" />
        <Footer />
      </div>
    </div>
  )
}
