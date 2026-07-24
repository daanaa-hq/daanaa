import React, { useEffect, useState, useMemo, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { DiscoveryProgress } from '../components/discovery/DiscoveryProgress'
import { DiscoveryQuestion } from '../components/discovery/DiscoveryQuestion'
import { DiscoveryChoice } from '../components/discovery/DiscoveryChoice'
import { DiscoveryResults } from '../components/discovery/DiscoveryResults'
import {
  DiscoveryState,
  encodeDiscoveryState,
  decodeDiscoveryState,
  mapToDirectoryFilters,
  explainInclusion,
  buildShortlist,
} from '../lib/discovery'
import { getOrganizations } from '../data/api'

declare global {
  interface Window {
    plausible?: (event: string, opts?: any) => void
  }
}

const CAUSE_TAXONOMY = {
  E: 'Education & Learning',
  P: 'Human Services',
  Y: 'Environment & Science',
  H: 'Health & Medicine',
  A: 'Arts & Culture',
  K: 'Religion & Spirituality',
}

const CAUSE_DETAILS = {
  E: { label: 'Education & Learning', category: 'Education' },
  P: { label: 'Human Services', category: 'Welfare' },
  Y: { label: 'Environment & Science', category: 'Science' },
  H: { label: 'Health & Medicine', category: 'Health' },
  A: { label: 'Arts & Culture', category: 'Arts' },
  K: { label: 'Religion & Spirituality', category: 'Religion' },
}

const PLACE_OPTIONS = [
  { id: 'nationwide', label: 'Anywhere in the United States' },
  { id: 'near-me', label: 'Near me' },
  { id: 'custom-zip', label: 'A city or ZIP code' },
  { id: 'custom-state', label: 'A specific state' },
]

const INTENT_OPTIONS = [
  { id: 'give-money', label: 'Give money', icon: '💰' },
  { id: 'volunteer', label: 'Give time', icon: '⏰' },
  { id: 'share-skills', label: 'Share knowledge or skills', icon: '🎓' },
  { id: 'learn', label: 'Learn about organizations in a community', icon: '📍' },
  { id: 'related', label: 'Find organizations working on related problems', icon: '🔗' },
]

const CONNECTION_OPTIONS = [
  {
    id: 'volunteer',
    label: 'A place to volunteer',
    description: 'Has known volunteer opportunities',
  },
  {
    id: 'website',
    label: 'A direct giving or organization website link',
    description: 'Has a verified website',
  },
  {
    id: 'smaller',
    label: 'A smaller, community-rooted organization',
    description: 'Budget under $700K annually',
  },
  {
    id: 'recent-filing',
    label: 'An organization with recent public filings',
    description: 'Filed tax info within the last 18 months',
  },
  {
    id: 'broad-mix',
    label: 'A broad mix so I can discover something new',
    description: 'Mix some unexpected choices into results',
  },
]

export default function GuidedDiscovery() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const [state, setState] = useState<DiscoveryState>({
    step: 1,
    intent: [],
    causes: [],
    place: 'nationwide',
    connection: [],
    mix: 'focused',
  })

  const [customPlace, setCustomPlace] = useState('')
  const [geolocating, setGeolocating] = useState(false)
  const [geoError, setGeoError] = useState('')
  const [showAnotherCount, setShowAnotherCount] = useState(0)  // Trigger refetch when "Show another" clicked

  // Seed for seeded random shuffle in discovery results
  const discoveryShuffleRef = useRef(Math.random().toString(36).slice(2, 11))

  const [results, setResults] = useState<any[]>([])
  const [resultGroups, setResultGroups] = useState<{
    closeMatches: any[]
    nearbyMatches: any[]
    discoveryMix: any[]
  }>({ closeMatches: [], nearbyMatches: [], discoveryMix: [] })
  const [loading, setLoading] = useState(false)
  const [explanations, setExplanations] = useState<Record<string, string>>({})
  const [shownOrgs, setShownOrgs] = useState<Set<string>>(new Set())  // Track shown orgs to avoid dupes

  // Decode URL params on mount
  useEffect(() => {
    const decoded = decodeDiscoveryState(searchParams)
    if (decoded.step) {
      setState((s) => ({ ...s, ...decoded, step: decoded.step as any }))
    }
  }, [])

  // Update URL when state changes
  useEffect(() => {
    const params = encodeDiscoveryState(state)
    setSearchParams(params)
  }, [state, setSearchParams])

  // Track analytics
  useEffect(() => {
    window.plausible?.('discovery_started')
  }, [])

  // Fetch results for step 5
  useEffect(() => {
    if (state.step !== 5) return

    const fetchResults = async () => {
      setLoading(true)
      try {
        const filters = mapToDirectoryFilters(state)
        // Generate a new seed when "Show another list" is clicked (showAnotherCount changes)
        if (showAnotherCount > 0) {
          discoveryShuffleRef.current = Math.random().toString(36).slice(2, 11)
        }

        const orgs = await getOrganizations({
          ntee: filters.ntee,
          state: filters.state,
          sort: 'random',
          seed: discoveryShuffleRef.current,
          per_page: 100,
        })

        const { closeMatches, nearbyMatches, discoveryMix } = buildShortlist(
          orgs.organizations || [],
          state
        )

        const allResults = [...closeMatches, ...nearbyMatches, ...discoveryMix]
        setResults(allResults)
        setResultGroups({ closeMatches, nearbyMatches, discoveryMix })

        // Don't mark as shown yet - only mark when "Show another list" is used
        // This allows generating fresh lists without exhausting the pool
        setShownOrgs(new Set())

        // Generate explanations
        const expl: Record<string, string> = {}
        allResults.forEach((org) => {
          expl[org.ein] = explainInclusion(org, state, CAUSE_TAXONOMY)
        })

        setExplanations(expl)

        window.plausible?.('result_list_shown', {
          props: { count: allResults.length, criteria: Object.keys(filters).length },
        })
      } catch (error) {
        console.error('Failed to fetch results:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [state, showAnotherCount])

  const handleContinue = () => {
    const stepNames = ['purpose', 'cause', 'place', 'connection', 'review']
    window.plausible?.('question_completed', {
      props: { question: stepNames[state.step - 1] },
    })

    if (state.step < 5) {
      setState((s) => ({ ...s, step: (s.step + 1) as any }))
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const handleBack = () => {
    if (state.step > 1) {
      setState((s) => ({ ...s, step: (s.step - 1) as any }))
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const handleStartOver = () => {
    setState({
      step: 1,
      intent: [],
      causes: [],
      place: 'nationwide',
      connection: [],
      mix: 'focused',
    })
    window.plausible?.('discovery_abandoned', { props: { step: state.step } })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleShowAnother = () => {
    // Increment counter to trigger refetch with same criteria but different random ordering
    setShowAnotherCount((c) => c + 1)
    window.plausible?.('another_list_requested')
  }

  const handleChangeAnswers = () => {
    setState((s) => ({ ...s, step: 1 }))
    window.plausible?.('criteria_changed')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleBrowseDirectory = () => {
    navigate('/directory')
  }

  // Step 1: Purpose
  if (state.step === 1) {
    const canContinue = state.intent.length > 0
    return (
      <div className="min-h-screen bg-warm-cream py-12">
        <div className="max-w-2xl mx-auto px-4">
          <DiscoveryProgress currentStep={1} />
          <DiscoveryQuestion
            heading="What brings you here?"
            subheading="You can choose more than one."
            canContinue={canContinue}
            onContinue={handleContinue}
            showBack={false}
            showStartOver={false}
          >
            <div className="space-y-3">
              {INTENT_OPTIONS.map((option) => (
                <DiscoveryChoice
                  key={option.id}
                  id={option.id}
                  label={option.label}
                  icon={option.icon}
                  selected={state.intent.includes(option.id)}
                  onChange={(selected) => {
                    if (selected) {
                      setState((s) => ({
                        ...s,
                        intent: [...s.intent, option.id],
                      }))
                    } else {
                      setState((s) => ({
                        ...s,
                        intent: s.intent.filter((i) => i !== option.id),
                      }))
                    }
                  }}
                  multiSelect={true}
                />
              ))}
            </div>
          </DiscoveryQuestion>
        </div>
      </div>
    )
  }

  // Step 2: Cause
  if (state.step === 2) {
    const canContinue = state.causes.length > 0
    const causeCodes = Object.entries(CAUSE_DETAILS).map(([code, data]) => ({
      code,
      label: data.label,
    }))

    return (
      <div className="min-h-screen bg-warm-cream py-12">
        <div className="max-w-2xl mx-auto px-4">
          <DiscoveryProgress currentStep={2} />
          <DiscoveryQuestion
            heading="What matters to you?"
            subheading="Choose one or more areas. You can change this later."
            canContinue={canContinue}
            onContinue={handleContinue}
            onBack={handleBack}
            onStartOver={handleStartOver}
            showBack={true}
            showStartOver={true}
          >
            <div className="space-y-3">
              {causeCodes.map(({ code, label }) => (
                <DiscoveryChoice
                  key={code}
                  id={code}
                  label={label}
                  selected={state.causes.includes(code)}
                  onChange={(selected) => {
                    if (selected) {
                      setState((s) => ({
                        ...s,
                        causes: [...s.causes, code],
                      }))
                    } else {
                      setState((s) => ({
                        ...s,
                        causes: s.causes.filter((c) => c !== code),
                      }))
                    }
                  }}
                  multiSelect={true}
                />
              ))}
            </div>
          </DiscoveryQuestion>
        </div>
      </div>
    )
  }

  // Step 3: Place
  if (state.step === 3) {
    const handleNearMe = () => {
      setGeoError('Coming soon! For now, use a city name or ZIP code above.')
    }

    const selectedPlaceId = state.place.split(':')[0]

    return (
      <div className="min-h-screen bg-warm-cream py-12">
        <div className="max-w-2xl mx-auto px-4">
          <DiscoveryProgress currentStep={3} />
          <DiscoveryQuestion
            heading="Where would you like to look?"
            canContinue={true}
            onContinue={handleContinue}
            onBack={handleBack}
            onStartOver={handleStartOver}
            showBack={true}
            showStartOver={true}
          >
            <div className="space-y-4">
              {/* Nationwide */}
              <DiscoveryChoice
                id="nationwide"
                label={PLACE_OPTIONS[0].label}
                selected={state.place === 'nationwide'}
                onChange={() => setState((s) => ({ ...s, place: 'nationwide' }))}
              />

              {/* Near me */}
              <button
                onClick={handleNearMe}
                disabled={geolocating}
                className={`
                  relative w-full text-left p-4 rounded-lg border-2 transition-all
                  ${
                    state.place === 'near-me'
                      ? 'border-deep-navy bg-muted-cream'
                      : 'border-light-grey bg-warm-cream hover:border-light-grey'
                  }
                  focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
              >
                <div className="flex items-start gap-3">
                  <div className={`
                    flex-shrink-0 mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center
                    ${
                      state.place === 'near-me'
                        ? 'border-deep-navy bg-muted-cream0'
                        : 'border-light-grey'
                    }
                  `}>
                    {state.place === 'near-me' && <span className="text-white text-xs">✓</span>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-deep-navy">
                      {geolocating ? 'Getting your location...' : PLACE_OPTIONS[1].label}
                    </h3>
                    {geoError && (
                      <p className="text-sm text-alert-amber mt-1">{geoError}</p>
                    )}
                  </div>
                </div>
              </button>

              {/* City/ZIP input */}
              <div className={`
                relative p-4 rounded-lg border-2 transition-all
                ${
                  selectedPlaceId === 'custom-zip'
                    ? 'border-deep-navy bg-muted-cream'
                    : 'border-light-grey bg-warm-cream'
                }
              `}>
                <label className="block font-medium text-deep-navy mb-2">
                  A city or ZIP code
                </label>
                <input
                  type="text"
                  placeholder="e.g., Houston, TX or 77001"
                  value={selectedPlaceId === 'custom-zip' ? customPlace : ''}
                  onChange={(e) => {
                    setCustomPlace(e.target.value)
                    if (e.target.value.trim()) {
                      setState((s) => ({ ...s, place: `custom-zip:${e.target.value.trim()}` }))
                    }
                  }}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>

              {/* State selector */}
              <div className={`
                relative p-4 rounded-lg border-2 transition-all
                ${
                  selectedPlaceId === 'custom-state'
                    ? 'border-deep-navy bg-muted-cream'
                    : 'border-light-grey bg-warm-cream'
                }
              `}>
                <label className="block font-medium text-deep-navy mb-2">
                  A specific state
                </label>
                <select
                  value={selectedPlaceId === 'custom-state' ? customPlace : ''}
                  onChange={(e) => {
                    setCustomPlace(e.target.value)
                    if (e.target.value) {
                      setState((s) => ({ ...s, place: `custom-state:${e.target.value}` }))
                    }
                  }}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="">Choose a state...</option>
                  <option value="CA">California</option>
                  <option value="TX">Texas</option>
                  <option value="NY">New York</option>
                  <option value="FL">Florida</option>
                  <option value="PA">Pennsylvania</option>
                  <option value="IL">Illinois</option>
                  <option value="OH">Ohio</option>
                  <option value="GA">Georgia</option>
                  <option value="NC">North Carolina</option>
                  <option value="MI">Michigan</option>
                  <option value="NJ">New Jersey</option>
                  <option value="VA">Virginia</option>
                  <option value="WA">Washington</option>
                  <option value="AZ">Arizona</option>
                  <option value="MA">Massachusetts</option>
                  <option value="TN">Tennessee</option>
                  <option value="IN">Indiana</option>
                  <option value="MD">Maryland</option>
                  <option value="MO">Missouri</option>
                  <option value="WI">Wisconsin</option>
                  <option value="CO">Colorado</option>
                  <option value="MN">Minnesota</option>
                  <option value="SC">South Carolina</option>
                  <option value="AL">Alabama</option>
                  <option value="LA">Louisiana</option>
                  <option value="KY">Kentucky</option>
                  <option value="OR">Oregon</option>
                  <option value="OK">Oklahoma</option>
                  <option value="CT">Connecticut</option>
                  <option value="UT">Utah</option>
                  <option value="AR">Arkansas</option>
                  <option value="NV">Nevada</option>
                  <option value="MS">Mississippi</option>
                  <option value="KS">Kansas</option>
                  <option value="NM">New Mexico</option>
                  <option value="NE">Nebraska</option>
                  <option value="ID">Idaho</option>
                  <option value="HI">Hawaii</option>
                  <option value="NH">New Hampshire</option>
                  <option value="ME">Maine</option>
                  <option value="RI">Rhode Island</option>
                  <option value="MT">Montana</option>
                  <option value="DE">Delaware</option>
                  <option value="SD">South Dakota</option>
                  <option value="ND">North Dakota</option>
                  <option value="AK">Alaska</option>
                  <option value="VT">Vermont</option>
                  <option value="WY">Wyoming</option>
                  <option value="WV">West Virginia</option>
                </select>
              </div>
            </div>
          </DiscoveryQuestion>
        </div>
      </div>
    )
  }

  // Step 4: Connection
  if (state.step === 4) {
    return (
      <div className="min-h-screen bg-warm-cream py-12">
        <div className="max-w-2xl mx-auto px-4">
          <DiscoveryProgress currentStep={4} />
          <DiscoveryQuestion
            heading="What kind of connection would help?"
            canContinue={true}
            onContinue={handleContinue}
            onBack={handleBack}
            onStartOver={handleStartOver}
            showBack={true}
            showStartOver={true}
          >
            <div className="space-y-3">
              {CONNECTION_OPTIONS.map((option) => (
                <DiscoveryChoice
                  key={option.id}
                  id={option.id}
                  label={option.label}
                  description={option.description}
                  selected={state.connection.includes(option.id) || (option.id === 'broad-mix' && state.mix === 'broad')}
                  onChange={(selected) => {
                    if (option.id === 'broad-mix') {
                      setState((s) => ({
                        ...s,
                        mix: selected ? 'broad' : 'focused',
                      }))
                    } else if (selected) {
                      setState((s) => ({
                        ...s,
                        connection: [...s.connection, option.id],
                      }))
                    } else {
                      setState((s) => ({
                        ...s,
                        connection: s.connection.filter((c) => c !== option.id),
                      }))
                    }
                  }}
                  multiSelect={true}
                />
              ))}
            </div>
          </DiscoveryQuestion>
        </div>
      </div>
    )
  }

  // Step 5: Results
  if (state.step === 5) {
    if (loading) {
      return (
        <div className="min-h-screen bg-warm-cream py-12 flex items-center justify-center">
          <div className="text-center">
            <div className="mb-4 text-4xl">🔍</div>
            <p className="text-cool-grey">Building your list...</p>
          </div>
        </div>
      )
    }

    return (
      <div className="min-h-screen bg-warm-cream py-12">
        <DiscoveryResults
          closeMatches={resultGroups.closeMatches}
          nearbyMatches={resultGroups.nearbyMatches}
          discoveryMix={resultGroups.discoveryMix}
          onShowAnother={handleShowAnother}
          onChangeAnswers={handleChangeAnswers}
          onStartOver={handleStartOver}
          onBrowseDirectory={handleBrowseDirectory}
          explanations={explanations}
        />
      </div>
    )
  }

  return null
}
