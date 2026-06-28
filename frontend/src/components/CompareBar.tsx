import { useNavigate } from 'react-router-dom'
import { useCompare, MAX_COMPARE } from '../contexts/CompareContext'

export default function CompareBar() {
  const { items, removeItem, clearItems } = useCompare()
  const navigate = useNavigate()

  if (items.length === 0) return null

  const handleCompare = () => {
    const eins = items.map(i => i.ein).join(',')
    navigate(`/compare?eins=${eins}`)
  }

  return (
    <div className="fixed bottom-[60px] md:bottom-0 left-0 right-0 z-40 px-4 py-3 bg-deep-navy border-t border-navy-mid shadow-2xl">
      <div className="max-w-[1200px] mx-auto flex items-center gap-3 flex-wrap">
        <span className="font-body text-[12px] text-warm-cream/60 shrink-0">
          Compare ({items.length}/{MAX_COMPARE}):
        </span>

        <div className="flex items-center gap-2 flex-wrap flex-1 min-w-0">
          {items.map(item => (
            <div
              key={item.ein}
              className="inline-flex items-center gap-1.5 pl-3 pr-2 py-1 rounded-full bg-white/8 border border-white/15"
            >
              <span className="font-body text-[12px] text-warm-cream truncate max-w-[140px]">{item.name}</span>
              <button
                onClick={() => removeItem(item.ein)}
                className="flex items-center justify-center w-4 h-4 rounded-full hover:bg-white/20 transition-colors shrink-0"
                aria-label={`Remove ${item.name}`}
              >
                <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="rgba(245,240,235,0.6)" strokeWidth="3" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          ))}

          {/* Empty slots */}
          {Array.from({ length: MAX_COMPARE - items.length }).map((_, i) => (
            <div
              key={`empty-${i}`}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-white/10 border-dashed"
            >
              <span className="font-body text-[12px] text-white/20">Add org</span>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={clearItems}
            className="font-body text-[13px] text-warm-cream/60 hover:text-warm-cream transition-colors"
          >
            Clear
          </button>
          <button
            onClick={handleCompare}
            disabled={items.length < 2}
            className="px-5 py-2 rounded-full bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Compare {items.length > 0 ? `(${items.length})` : ''}
          </button>
        </div>
      </div>
    </div>
  )
}
