import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'

export interface ClaimState {
  ein: string
  email: string
  orgName: string | null
  irsAddress: string | null
  verificationToken: string | null
  pinEntered: boolean
  customMission: string
  customDescription: string
  causeTagsJson: string
  donateConfirmed: boolean
  loading: boolean
  error: string | null
}

export function useClaimFlow() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [state, setState] = useState<ClaimState>({
    ein: searchParams.get('ein') || '',
    email: searchParams.get('email') || '',
    orgName: searchParams.get('orgName') || null,
    irsAddress: searchParams.get('irsAddress') || null,
    verificationToken: searchParams.get('token') || null,
    pinEntered: false,
    customMission: '',
    customDescription: '',
    causeTagsJson: '[]',
    donateConfirmed: false,
    loading: false,
    error: null,
  })

  // Verify PIN via API
  async function verifyPin(pin: string): Promise<boolean> {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const res = await fetch('/api/claim/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein: state.ein, pin }),
      })
      const body = await res.json()
      if (!res.ok) {
        setState(s => ({ ...s, error: body.error || 'Verification failed', loading: false }))
        return false
      }
      const token = body.verification_token || pin
      setState(s => ({
        ...s,
        verificationToken: token,
        pinEntered: true,
        loading: false,
      }))
      return true
    } catch (e) {
      setState(s => ({ ...s, error: 'Network error. Please try again.', loading: false }))
      return false
    }
  }

  // Update claim with custom fields
  async function updateClaim(fields: Partial<ClaimState>): Promise<boolean> {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const res = await fetch('/api/claim/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein: state.ein,
          verification_token: state.verificationToken,
          custom_mission: fields.customMission || state.customMission,
          custom_description: fields.customDescription || state.customDescription,
          cause_tags_json: fields.causeTagsJson || state.causeTagsJson,
          donate_confirmed: fields.donateConfirmed ?? state.donateConfirmed,
        }),
      })
      const body = await res.json()
      if (!res.ok) {
        setState(s => ({ ...s, error: body.error || 'Update failed', loading: false }))
        return false
      }
      setState(s => ({ ...s, ...fields, loading: false }))
      return true
    } catch (e) {
      setState(s => ({ ...s, error: 'Network error. Please try again.', loading: false }))
      return false
    }
  }

  return {
    state,
    setState,
    verifyPin,
    updateClaim,
  }
}
