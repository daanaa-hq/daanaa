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
        <div className="max-w-5xl mx-auto px-8 pt-8"><div className="bg-white border border-light-grey rounded-2xl p-6"><p className="font-body text-[11px] font-medium tracking-[0.10em] text-deep-gold uppercase mb-2">Public working library</p><h1 className="font-display italic text-deep-navy text-3xl mb-2">Daanaa research papers</h1><p className="font-body text-[14px] text-cool-grey leading-[1.7] mb-4">Working papers about the questions behind Daanaa, shared openly for nonprofit, academic, donor, and community review. They are works in progress, not institutional endorsements.</p><div className="flex flex-wrap gap-3"><a href="/pages/daanaa-vision.html" className="font-body text-[13px] font-semibold text-deep-gold hover:text-soft-gold">The Daanaa Vision →</a><a href="/pages/ai-governance.html" className="font-body text-[13px] font-semibold text-deep-gold hover:text-soft-gold">AI Governance →</a><a href="/pages/peer-financial-context.html" className="font-body text-[13px] font-semibold text-deep-gold hover:text-soft-gold">Peer Financial Context →</a></div></div></div>
        <ResearchContent sessionToken="" />
      </div>
    </div>
  )
}
