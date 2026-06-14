interface ResearchSidebarProps {
  currentSection: string
  onSectionChange: (sectionId: string) => void
}

const SECTIONS = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'about', label: 'About Daanaa', icon: '🎯' },
  { id: 'problem', label: 'The Discovery Problem', icon: '🔍' },
  { id: 'methodology', label: 'Our Methodology', icon: '📐' },
  { id: 'operating-models', label: 'Operating Models & Bands', icon: '⚙️' },
  { id: 'financial-archetypes', label: 'Financial Archetypes', icon: '📈' },
  { id: 'entity-types', label: 'Organization Types', icon: '🏛️' },
  { id: 'peer-context', label: 'Peer Financial Context', icon: '💰' },
  { id: 'findings', label: 'Research Findings', icon: '📚' },
  { id: 'spending', label: 'Program Spending', icon: '💸' },
]

export default function ResearchSidebar({
  currentSection,
  onSectionChange,
}: ResearchSidebarProps) {
  return (
    <aside className="w-64 bg-deep-navy text-warm-cream sticky top-0 h-screen overflow-y-auto border-r border-soft-gold/20 p-6">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <img
            src="/logo.png"
            alt="Daanaa"
            className="h-8 w-8 object-contain"
            width={32}
            height={32}
          />
          <h2 className="text-2xl font-display text-soft-gold">Research</h2>
        </div>
        <p className="text-xs text-cool-grey">Advisor & academic guide</p>
      </div>

      <nav className="space-y-2">
        {SECTIONS.map((section) => (
          <button
            key={section.id}
            onClick={() => onSectionChange(section.id)}
            className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all ${
              currentSection === section.id
                ? 'bg-soft-gold text-deep-navy font-semibold'
                : 'text-warm-cream hover:bg-deep-navy/50'
            }`}
          >
            <span className="mr-2">{section.icon}</span>
            {section.label}
          </button>
        ))}
      </nav>

      <div className="mt-8 pt-6 border-t border-soft-gold/20">
        <p className="text-xs text-cool-grey">
          This research area is intended for advisor, academic, nonprofit, and
          foundation review.
        </p>
      </div>
    </aside>
  )
}
