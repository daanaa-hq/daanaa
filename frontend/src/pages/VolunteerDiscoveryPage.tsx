import React, { useState, useEffect, useMemo } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import Breadcrumb from '../components/Breadcrumb'
import VolunteerInterest from '../components/VolunteerInterest'
import { getNteeLabel } from '../data/ntee'
import { API_BASE } from '../lib/platform'

interface VolunteerEvent {
  id: number
  ein: string
  organization_name: string
  org_mission?: string
  title: string
  description?: string
  event_date: string
  start_time?: string
  is_virtual: boolean
  location_city?: string
  location_state?: string
  location_zip?: string
  event_type?: string
  contact_email?: string
  signup_url?: string
  signup_count: number
}

interface FilterState {
  location: 'all' | 'virtual' | 'inperson'
  state: string
  city: string
  category: string
  dateFrom: string
  dateTo: string
}

export default function VolunteerDiscoveryPage() {
  usePageMeta(
    'Volunteer Opportunities | Daanaa',
    'Discover volunteer opportunities at nonprofits. Find causes you care about and express interest.'
  )

  const [events, setEvents] = useState<VolunteerEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState<FilterState>({
    location: 'all',
    state: '',
    city: '',
    category: '',
    dateFrom: '',
    dateTo: '',
  })
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState<VolunteerEvent | null>(null)

  const limit = 20

  useEffect(() => {
    setOffset(0)
    setEvents([])
  }, [filters])

  useEffect(() => {
    if (!hasMore && offset > 0) return

    setLoading(true)
    const params = new URLSearchParams()
    if (filters.state) params.append('state', filters.state)
    if (filters.city) params.append('city', filters.city)
    if (filters.category) params.append('ntee', filters.category)
    if (filters.location === 'virtual') params.append('virtual', '1')
    if (filters.dateFrom) params.append('date_from', filters.dateFrom)
    if (filters.dateTo) params.append('date_to', filters.dateTo)
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    fetch(`${API_BASE}/api/volunteer-events?${params}`)
      .then(r => r.json())
      .then(data => {
        if (offset === 0) {
          setEvents(data.events || [])
        } else {
          setEvents(prev => [...prev, ...data.events || []])
        }
        setHasMore((data.events || []).length === limit)
      })
      .catch(err => {
        console.error('Failed to fetch events:', err)
        setHasMore(false)
      })
      .finally(() => setLoading(false))
  }, [offset, filters, hasMore])

  const states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
  const categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

  const uniqueCities = useMemo(() => {
    if (!filters.state) return []
    return [...new Set(events
      .filter(e => e.location_state === filters.state)
      .map(e => e.location_city)
      .filter(Boolean)
    )].sort()
  }, [events, filters.state])

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      <Breadcrumb items={[
        { label: 'Home', href: '/' },
        { label: 'Volunteer' }
      ]} />

      {/* Header */}
      <div className="bg-deep-navy text-warm-cream py-12 px-6">
        <div className="max-w-[1200px] mx-auto">
          <h1 className="font-display italic text-display leading-tight mb-3">
            Volunteer with Purpose
          </h1>
          <p className="font-body text-lead text-muted-cream max-w-[600px]">
            Find organizations working on causes you care about. Browse opportunities, express interest, and start making a difference.
          </p>
        </div>
      </div>

      {/* Filters + Results */}
      <div className="max-w-[1200px] mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-8">
          {/* Filters */}
          <div className="bg-white rounded-xl p-6 border border-light-grey h-fit sticky top-24">
            <h3 className="font-semibold text-deep-navy mb-4">Filters</h3>

            <div className="space-y-4">
              {/* Location type */}
              <div>
                <label className="block font-body text-caption font-semibold text-deep-navy mb-2">Type</label>
                <div className="space-y-1.5">
                  {['all', 'virtual', 'inperson'].map(type => (
                    <label key={type} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={filters.location === type}
                        onChange={() => setFilters(f => ({ ...f, location: type as FilterState['location'] }))}
                      />
                      <span className="font-body text-small text-cool-grey capitalize">
                        {type === 'all' ? 'All' : type === 'virtual' ? 'Virtual' : 'In Person'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* State */}
              <div>
                <label className="block font-body text-caption font-semibold text-deep-navy mb-2">State</label>
                <select
                  value={filters.state}
                  onChange={e => setFilters(f => ({ ...f, state: e.target.value, city: '' }))}
                  className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-small"
                >
                  <option value="">All states</option>
                  {states.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              {/* City */}
              {filters.state && uniqueCities.length > 0 && (
                <div>
                  <label className="block font-body text-caption font-semibold text-deep-navy mb-2">City</label>
                  <select
                    value={filters.city}
                    onChange={e => setFilters(f => ({ ...f, city: e.target.value }))}
                    className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-small"
                  >
                    <option value="">All cities</option>
                    {uniqueCities.map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Category */}
              <div>
                <label className="block font-body text-caption font-semibold text-deep-navy mb-2">Cause Area</label>
                <select
                  value={filters.category}
                  onChange={e => setFilters(f => ({ ...f, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-small"
                >
                  <option value="">All causes</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{getNteeLabel(cat)}</option>
                  ))}
                </select>
              </div>

              {/* Date range */}
              <div>
                <label className="block font-body text-caption font-semibold text-deep-navy mb-2">Date From</label>
                <input
                  type="date"
                  value={filters.dateFrom}
                  onChange={e => setFilters(f => ({ ...f, dateFrom: e.target.value }))}
                  className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-small"
                />
              </div>

              <div>
                <label className="block font-body text-caption font-semibold text-deep-navy mb-2">Date To</label>
                <input
                  type="date"
                  value={filters.dateTo}
                  onChange={e => setFilters(f => ({ ...f, dateTo: e.target.value }))}
                  className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-small"
                />
              </div>
            </div>
          </div>

          {/* Events grid */}
          <div>
            <p className="font-body text-small text-cool-grey mb-6">
              {events.length} opportunities found
            </p>

            {events.length === 0 && !loading && (
              <div className="text-center py-12">
                <p className="font-body text-body text-cool-grey">No opportunities match your filters.</p>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {events.map(event => {
                const eventDate = new Date(event.event_date)
                const dateStr = eventDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
                const location = event.is_virtual
                  ? 'Virtual'
                  : [event.location_city, event.location_state].filter(Boolean).join(', ')

                return (
                  <div key={event.id} className="bg-white rounded-xl border border-light-cream p-5 flex flex-col gap-3">
                    <div>
                      <span className={`inline-block px-2 py-0.5 rounded-full font-body text-micro font-semibold tracking-[0.06em] uppercase mb-1 ${
                        event.is_virtual ? 'bg-blue-50 text-blue-600' : 'bg-soft-gold/15 text-deep-gold'
                      }`}>
                        {event.is_virtual ? 'Virtual' : 'In Person'}
                      </span>
                      <h3 className="font-display italic text-deep-navy text-title-sm leading-tight">{event.title}</h3>
                      <p className="font-body text-caption text-cool-grey mt-0.5">
                        {dateStr}{location ? ` · ${location}` : ''}
                      </p>
                    </div>

                    {event.organization_name && (
                      <p className="font-body text-caption text-cool-grey font-medium">
                        {event.organization_name}
                      </p>
                    )}

                    {event.description && (
                      <p className="font-body text-small text-cool-grey leading-[1.6] line-clamp-2">{event.description}</p>
                    )}

                    {event.signup_count > 0 && (
                      <p className="font-body text-label text-muted-cream">
                        {event.signup_count} {event.signup_count === 1 ? 'person' : 'people'} interested
                      </p>
                    )}

                    <div className="mt-auto">
                      <button
                        onClick={() => setSelectedEvent(event)}
                        className="inline-flex items-center gap-1.5 px-3 py-2 border border-soft-gold text-soft-gold rounded-lg font-body text-small font-semibold hover:bg-soft-gold/10 transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                        </svg>
                        Express interest
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            {loading && (
              <div className="text-center py-8">
                <p className="font-body text-small text-cool-grey">Loading...</p>
              </div>
            )}

            {hasMore && !loading && (
              <button
                onClick={() => setOffset(prev => prev + limit)}
                className="w-full mt-8 py-3 rounded-lg border border-soft-gold text-soft-gold font-body text-body font-semibold hover:bg-soft-gold/10 transition-colors"
              >
                Load more
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Volunteer Interest Modal */}
      {selectedEvent && (
        <VolunteerInterest
          orgName={selectedEvent.organization_name || 'Unknown'}
          website={undefined}
          contactEmail={selectedEvent.contact_email}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  )
}
