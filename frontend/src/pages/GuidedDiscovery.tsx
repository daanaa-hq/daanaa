import React, { useEffect, useState, useMemo } from 'react'
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

  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [explanations, setExplanations] = useState<Record<string, string>>({})

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
        const orgs = await getOrganizations({
          ntee: filters.ntee,
          state: filters.state,
          per_page: 100,
        })

        const { closeMatches, nearbyMatches, discoveryMix } = buildShortlist(
          orgs.organizations || [],
          state
        )

        const allResults = [...closeMatches, ...nearbyMatches, ...discoveryMix]
        setResults(allResults)

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
  }, [state])

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
    // Shuffle results without changing criteria
    const { closeMatches, nearbyMatches, discoveryMix } = buildShortlist(results, state)
    const allResults = [...closeMatches, ...nearbyMatches, ...discoveryMix]
    setResults(allResults)

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
      <div className="min-h-screen bg-white dark:bg-gray-900 py-12">
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
      <div className="min-h-screen bg-white dark:bg-gray-900 py-12">
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
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 py-12">
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
            <div className="space-y-3">
              {PLACE_OPTIONS.map((option) => (
                <DiscoveryChoice
                  key={option.id}
                  id={option.id}
                  label={option.label}
                  selected={state.place === option.id || state.place.startsWith(option.id + ':')}
                  onChange={() => {
                    if (option.id === 'nationwide') {
                      setState((s) => ({ ...s, place: 'nationwide' }))
                    } else if (option.id === 'near-me') {
                      setState((s) => ({ ...s, place: 'near-me' }))
                    } else {
                      // For custom zip/state, show input (simplified for now)
                      setState((s) => ({ ...s, place: 'nationwide' }))
                    }
                  }}
                />
              ))}
            </div>
          </DiscoveryQuestion>
        </div>
      </div>
    )
  }

  // Step 4: Connection
  if (state.step === 4) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 py-12">
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
        <div className="min-h-screen bg-white dark:bg-gray-900 py-12 flex items-center justify-center">
          <div className="text-center">
            <div className="mb-4 text-4xl">🔍</div>
            <p className="text-gray-600 dark:text-gray-400">Building your list...</p>
          </div>
        </div>
      )
    }

    const closeMatches = results.slice(0, Math.ceil(results.length * 0.5))
    const nearbyMatches = results.slice(
      Math.ceil(results.length * 0.5),
      Math.ceil(results.length * 0.85)
    )
    const discoveryMix = results.slice(Math.ceil(results.length * 0.85))

    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 py-12">
        <DiscoveryResults
          closeMatches={closeMatches}
          nearbyMatches={nearbyMatches}
          discoveryMix={discoveryMix}
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
