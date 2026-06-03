# Nonprofit Claiming Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete self-service flow for nonprofits to claim their profile, verify ownership via email PIN, and edit their mission, donation link, and cause tags.

**Architecture:** Three new React pages wire into the existing API claim endpoints (`/api/claim/start`, `/api/claim/verify`, `/api/claim/update`). The ForNonprofits page already handles the initial email/EIN submission; ClaimVerify handles PIN entry and verification; OrgClaimEditor handles profile customization. All state is React-local with API posts to persist changes.

**Tech Stack:** React 19 + TypeScript, React Router, Radix UI + Tailwind, fetch API, Zod for input validation.

---

## File Structure

| File | Responsibility |
|------|-----------------|
| `frontend/src/pages/ClaimVerify.tsx` | PIN entry, verification, routing to editor |
| `frontend/src/pages/OrgClaimEditor.tsx` | Edit mission, donation link, cause tags, save changes |
| `frontend/src/pages/ClaimSuccess.tsx` | Confirmation page after successful claim |
| `frontend/src/components/ClaimProgressBar.tsx` | Visual progress indicator (email → PIN → edit → done) |
| `frontend/src/hooks/useClaimFlow.ts` | Shared state + API calls for the claiming flow |

---

## Task 1: Create useClaimFlow hook

**Files:**
- Create: `frontend/src/hooks/useClaimFlow.ts`

This hook manages claiming state and API calls shared across multiple pages.

- [ ] **Step 1: Write the hook with test structure**

Create `frontend/src/hooks/useClaimFlow.ts`:

```typescript
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
```

- [ ] **Step 2: Verify hook compiles**

```bash
cd /home/akbar/meritgiving/frontend
npm run build 2>&1 | grep -E "(error|warning)" | head -20
```

Expected: No TypeScript errors for the new hook.

- [ ] **Step 3: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/src/hooks/useClaimFlow.ts
git commit -m "feat: add useClaimFlow hook for claiming state management"
```

---

## Task 2: Create ClaimProgressBar component

**Files:**
- Create: `frontend/src/components/ClaimProgressBar.tsx`

Visual indicator showing progress through the claiming flow (steps 1–4).

- [ ] **Step 1: Write the component**

Create `frontend/src/components/ClaimProgressBar.tsx`:

```typescript
import React from 'react'

export interface ClaimProgressBarProps {
  currentStep: 'email' | 'verify' | 'edit' | 'success'
}

const STEPS = [
  { key: 'email', label: 'Email' },
  { key: 'verify', label: 'Verify PIN' },
  { key: 'edit', label: 'Edit Profile' },
  { key: 'success', label: 'Done' },
]

export function ClaimProgressBar({ currentStep }: ClaimProgressBarProps) {
  const currentIndex = STEPS.findIndex(s => s.key === currentStep)

  return (
    <div className="w-full">
      {/* Progress bar */}
      <div className="flex gap-4 mb-8">
        {STEPS.map((step, idx) => (
          <div key={step.key} className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-body text-[13px] font-bold transition-colors ${
                  idx <= currentIndex
                    ? 'bg-soft-gold text-deep-navy'
                    : 'bg-light-cream text-muted-cream'
                }`}
              >
                {idx + 1}
              </div>
              <span
                className={`font-body text-[13px] font-medium ${
                  idx === currentIndex
                    ? 'text-deep-navy'
                    : idx < currentIndex
                    ? 'text-muted-cream'
                    : 'text-light-cream'
                }`}
              >
                {step.label}
              </span>
            </div>
            {idx < STEPS.length - 1 && (
              <div
                className={`h-1 ml-4 transition-colors ${
                  idx < currentIndex ? 'bg-soft-gold' : 'bg-light-cream'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify component compiles**

```bash
cd /home/akbar/meritgiving/frontend
npm run build 2>&1 | grep -E "ClaimProgressBar" | head -5
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/src/components/ClaimProgressBar.tsx
git commit -m "feat: add ClaimProgressBar visual component"
```

---

## Task 3: Create ClaimVerify page (PIN entry)

**Files:**
- Create: `frontend/src/pages/ClaimVerify.tsx`

Handles PIN entry, verification, and routing to the editor page.

- [ ] **Step 1: Write the page**

Create `frontend/src/pages/ClaimVerify.tsx`:

```typescript
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'
import { useClaimFlow } from '../hooks/useClaimFlow'
import { AlertCircle, Check } from 'lucide-react'

export default function ClaimVerify() {
  usePageMeta('Verify Claim', 'Enter the PIN from your verification email to claim your nonprofit profile.')
  
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { state, verifyPin } = useClaimFlow()
  const [pin, setPin] = useState('')
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    // If no email in URL params, redirect back to start
    const emailParam = searchParams.get('email')
    const einParam = searchParams.get('ein')
    if (!emailParam || !einParam) {
      navigate('/for-nonprofits', { replace: true })
    }
  }, [searchParams, navigate])

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault()
    if (!pin.trim()) return
    
    setVerifying(true)
    const success = await verifyPin(pin)
    setVerifying(false)

    if (success) {
      // Navigate to editor with token in URL
      navigate(`/claim/edit?ein=${encodeURIComponent(state.ein)}&token=${encodeURIComponent(state.verificationToken || pin)}`)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-gradient-to-br from-warm-cream to-light-cream">
      <div className="max-w-[520px] mx-auto px-6 py-12 lg:py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-display italic text-deep-navy mb-3" style={{ fontSize: 'clamp(32px, 5vw, 48px)' }}>
            Verify your email
          </h1>
          <p className="font-body text-[16px] text-muted-cream">
            We sent a PIN to <strong>{searchParams.get('email')}</strong>. Enter it below to continue.
          </p>
        </div>

        {/* Progress */}
        <ClaimProgressBar currentStep="verify" />

        {/* PIN Form */}
        <form onSubmit={handleVerify} className="bg-white rounded-lg shadow-sm border border-light-cream p-8">
          {state.error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <p className="font-body text-[14px] text-red-700">{state.error}</p>
            </div>
          )}

          <label className="block mb-6">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">6-digit PIN</span>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="w-full px-4 py-3 border border-light-cream rounded-lg font-body text-[16px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
              disabled={verifying}
            />
          </label>

          <button
            type="submit"
            disabled={pin.length !== 6 || verifying}
            className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-lg hover:bg-bright-gold disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {verifying ? (
              <>
                <div className="w-4 h-4 rounded-full border-2 border-deep-navy border-t-transparent animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Verify PIN
              </>
            )}
          </button>

          <p className="mt-6 font-body text-[13px] text-muted-cream text-center">
            Didn't get the email? Check your spam folder or{' '}
            <button
              type="button"
              onClick={() => navigate('/for-nonprofits')}
              className="text-soft-gold hover:text-bright-gold font-semibold"
            >
              try again
            </button>
          </p>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Update App.tsx to pass claimVerify**

The route is already defined. Verify the import works by building:

```bash
cd /home/akbar/meritgiving/frontend
npm run build 2>&1 | grep -i "claimverify\|error" | head -10
```

Expected: No errors related to ClaimVerify.

- [ ] **Step 3: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/src/pages/ClaimVerify.tsx
git commit -m "feat: add ClaimVerify page with PIN entry and verification"
```

---

## Task 4: Create OrgClaimEditor page

**Files:**
- Create: `frontend/src/pages/OrgClaimEditor.tsx`

Allows nonprofits to edit their mission, donation link, and cause tags after PIN verification.

- [ ] **Step 1: Write the page**

Create `frontend/src/pages/OrgClaimEditor.tsx`:

```typescript
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'
import { useClaimFlow } from '../hooks/useClaimFlow'
import { AlertCircle, Check } from 'lucide-react'

const CAUSE_TAGS_OPTIONS = [
  'Arts & Culture',
  'Education',
  'Environment',
  'Health',
  'Community Development',
  'Human Rights',
  'Research',
  'International Aid',
  'Animals',
  'Disaster Relief',
]

export default function OrgClaimEditor() {
  usePageMeta('Edit Your Profile', 'Add your mission, donation link, and impact areas.')
  
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { state, setState, updateClaim } = useClaimFlow()
  const [mission, setMission] = useState('')
  const [description, setDescription] = useState('')
  const [donateUrl, setDonateUrl] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    // Redirect if not verified
    const tokenParam = searchParams.get('token')
    const einParam = searchParams.get('ein')
    if (!tokenParam || !einParam) {
      navigate('/for-nonprofits', { replace: true })
    }
  }, [searchParams, navigate])

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)

    const success = await updateClaim({
      customMission: mission,
      customDescription: description,
      causeTagsJson: JSON.stringify(selectedTags),
      donateConfirmed: donateUrl.length > 0,
    })

    setSaving(false)

    if (success) {
      navigate(`/claim/success?ein=${encodeURIComponent(state.ein)}`)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-gradient-to-br from-warm-cream to-light-cream">
      <div className="max-w-[520px] mx-auto px-6 py-12 lg:py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-display italic text-deep-navy mb-3" style={{ fontSize: 'clamp(32px, 5vw, 48px)' }}>
            Make your story visible
          </h1>
          <p className="font-body text-[16px] text-muted-cream">
            Add the details only your organization can share. All fields are optional.
          </p>
        </div>

        {/* Progress */}
        <ClaimProgressBar currentStep="edit" />

        {/* Edit Form */}
        <form onSubmit={handleSave} className="bg-white rounded-lg shadow-sm border border-light-cream p-8 space-y-6">
          {state.error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <p className="font-body text-[14px] text-red-700">{state.error}</p>
            </div>
          )}

          {/* Mission */}
          <label className="block">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">
              Mission statement (1–2 sentences)
            </span>
            <textarea
              value={mission}
              onChange={(e) => setMission(e.target.value.slice(0, 300))}
              placeholder="What does your organization do?"
              rows={3}
              className="w-full px-4 py-3 border border-light-cream rounded-lg font-body text-[14px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-none"
              disabled={saving}
            />
            <p className="mt-1 font-body text-[12px] text-muted-cream">{mission.length} / 300</p>
          </label>

          {/* Description */}
          <label className="block">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">
              Impact notes (programs, service area, leadership)
            </span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value.slice(0, 500))}
              placeholder="Describe your programs and impact..."
              rows={4}
              className="w-full px-4 py-3 border border-light-cream rounded-lg font-body text-[14px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-none"
              disabled={saving}
            />
            <p className="mt-1 font-body text-[12px] text-muted-cream">{description.length} / 500</p>
          </label>

          {/* Donation URL */}
          <label className="block">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">
              Verified donation link (optional)
            </span>
            <input
              type="url"
              value={donateUrl}
              onChange={(e) => setDonateUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-4 py-3 border border-light-cream rounded-lg font-body text-[14px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
              disabled={saving}
            />
            <p className="mt-1 font-body text-[12px] text-muted-cream">
              Provide your official donation link for donors to contribute directly.
            </p>
          </label>

          {/* Cause Tags */}
          <fieldset>
            <legend className="block font-body text-[13px] font-medium text-deep-navy mb-3">
              Impact areas (select all that apply)
            </legend>
            <div className="grid grid-cols-2 gap-3">
              {CAUSE_TAGS_OPTIONS.map((tag) => (
                <label key={tag} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedTags.includes(tag)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTags([...selectedTags, tag])
                      } else {
                        setSelectedTags(selectedTags.filter((t) => t !== tag))
                      }
                    }}
                    disabled={saving}
                    className="w-4 h-4 rounded border-light-cream accent-soft-gold cursor-pointer"
                  />
                  <span className="font-body text-[13px] text-deep-navy">{tag}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Save Button */}
          <button
            type="submit"
            disabled={saving}
            className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-lg hover:bg-bright-gold disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 mt-8"
          >
            {saving ? (
              <>
                <div className="w-4 h-4 rounded-full border-2 border-deep-navy border-t-transparent animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Save profile
              </>
            )}
          </button>

          <p className="font-body text-[12px] text-muted-cream text-center">
            You can return anytime to edit your profile.
          </p>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify the page compiles**

```bash
cd /home/akbar/meritgiving/frontend
npm run build 2>&1 | grep -E "OrgClaimEditor|error" | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/src/pages/OrgClaimEditor.tsx
git commit -m "feat: add OrgClaimEditor page for profile customization"
```

---

## Task 5: Create ClaimSuccess page

**Files:**
- Create: `frontend/src/pages/ClaimSuccess.tsx`

Confirmation page showing successful claim.

- [ ] **Step 1: Write the page**

Create `frontend/src/pages/ClaimSuccess.tsx`:

```typescript
import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'
import { Check, ArrowRight } from 'lucide-react'

export default function ClaimSuccess() {
  usePageMeta('Claim Successful', 'Your nonprofit profile is now claimed and visible.')
  
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const ein = searchParams.get('ein')

  useEffect(() => {
    if (!ein) {
      navigate('/for-nonprofits', { replace: true })
    }
  }, [ein, navigate])

  return (
    <div className="min-h-[100dvh] bg-gradient-to-br from-warm-cream to-light-cream">
      <div className="max-w-[520px] mx-auto px-6 py-12 lg:py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="w-16 h-16 rounded-full bg-soft-gold text-deep-navy mx-auto mb-6 flex items-center justify-center">
            <Check className="w-8 h-8" />
          </div>
          <h1 className="font-display italic text-deep-navy mb-3" style={{ fontSize: 'clamp(32px, 5vw, 48px)' }}>
            Your profile is live
          </h1>
          <p className="font-body text-[16px] text-muted-cream">
            Thank you for claiming your nonprofit profile. Your mission, programs, and giving links are now visible to donors.
          </p>
        </div>

        {/* Progress */}
        <ClaimProgressBar currentStep="success" />

        {/* Success Content */}
        <div className="bg-white rounded-lg shadow-sm border border-light-cream p-8 space-y-6">
          <div className="space-y-4">
            <div className="flex gap-4 items-start">
              <div className="w-6 h-6 rounded-full bg-soft-gold text-deep-navy flex items-center justify-center shrink-0 mt-0.5 font-body text-[13px] font-bold">
                ✓
              </div>
              <div>
                <p className="font-body font-medium text-deep-navy mb-1">Profile claimed</p>
                <p className="font-body text-[13px] text-muted-cream">
                  Your organization is now marked as verified on Daanaa.
                </p>
              </div>
            </div>

            <div className="flex gap-4 items-start">
              <div className="w-6 h-6 rounded-full bg-soft-gold text-deep-navy flex items-center justify-center shrink-0 mt-0.5 font-body text-[13px] font-bold">
                ✓
              </div>
              <div>
                <p className="font-body font-medium text-deep-navy mb-1">Mission visible</p>
                <p className="font-body text-[13px] text-muted-cream">
                  Your mission, programs, and giving links are live for donors.
                </p>
              </div>
            </div>

            <div className="flex gap-4 items-start">
              <div className="w-6 h-6 rounded-full bg-soft-gold text-deep-navy flex items-center justify-center shrink-0 mt-0.5 font-body text-[13px] font-bold">
                ✓
              </div>
              <div>
                <p className="font-body font-medium text-deep-navy mb-1">Editable anytime</p>
                <p className="font-body text-[13px] text-muted-cream">
                  You can return to edit your profile whenever you need.
                </p>
              </div>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col gap-3 pt-4">
            <Link
              to={`/org/${ein}`}
              className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-lg hover:bg-bright-gold transition-colors flex items-center justify-center gap-2"
            >
              View your profile
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/"
              className="w-full px-4 py-3 border border-light-cream text-deep-navy font-body text-[14px] font-semibold rounded-lg hover:bg-light-cream transition-colors"
            >
              Return home
            </Link>
          </div>
        </div>

        <p className="text-center font-body text-[12px] text-muted-cream mt-8">
          Have questions?{' '}
          <a href="mailto:support@daanaa.org" className="text-soft-gold hover:text-bright-gold font-semibold">
            Contact us
          </a>
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify the page compiles**

```bash
cd /home/akbar/meritgiving/frontend
npm run build 2>&1 | grep -E "ClaimSuccess|error" | head -10
```

Expected: No errors.

- [ ] **Step 3: Update App.tsx with the new route**

Edit `frontend/src/App.tsx`:

```typescript
const ClaimSuccess = lazy(() => import('./pages/ClaimSuccess'))
```

Add to the routes before the `<Route path="/admin"...>` line:

```typescript
<Route path="/claim/success" element={<ClaimSuccess />} />
```

- [ ] **Step 4: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/src/pages/ClaimSuccess.tsx frontend/src/App.tsx
git commit -m "feat: add ClaimSuccess confirmation page"
```

---

## Task 6: Update ForNonprofits page to route to PIN verification

**Files:**
- Modify: `frontend/src/pages/ForNonprofits.tsx`

After successful submission, navigate to the PIN verification page.

- [ ] **Step 1: Locate the success handler**

In `ForNonprofits.tsx`, find the `handleSubmit` function (around line 46). After the API call succeeds (line 62), add navigation:

```typescript
if (body.org_name) setOrgName(body.org_name)
setAddressPreview(body.address_preview || irsAddress)
setSubmitted(true)

// NEW: Navigate to verification page
const params = new URLSearchParams({
  ein: ein.replace(/\D/g, '').slice(0, 9),
  email: email.trim(),
  orgName: body.org_name || orgName || '',
  irsAddress: body.address_preview || irsAddress || '',
})
setTimeout(() => {
  window.location.href = `/claim/verify?${params.toString()}`
}, 1000)
```

- [ ] **Step 2: Edit the file**

Open the file and make the change:

```bash
# Verify the location first
grep -n "setSubmitted(true)" /home/akbar/meritgiving/frontend/src/pages/ForNonprofits.tsx
```

Should return line ~65.

- [ ] **Step 3: Apply the edit**

Using the Edit tool, modify the success handler in ForNonprofits.tsx to add navigation to ClaimVerify.

- [ ] **Step 4: Test build**

```bash
cd /home/akbar/meritgiving/frontend
npm run build 2>&1 | grep -E "error|warning" | head -10
```

Expected: No new errors.

- [ ] **Step 5: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/src/pages/ForNonprofits.tsx
git commit -m "feat: navigate to PIN verification after email submission"
```

---

## Task 7: Verify API endpoints exist and handle updates

**Files:**
- Review: `merit_api.py` (lines with `/api/claim/*` endpoints)

The backend already has `claim_start()` and `claim_verify()`. Verify `claim_update()` exists for profile edits.

- [ ] **Step 1: Search for claim_update endpoint**

```bash
grep -n "def claim_update\|@app.route.*claim.*update" /home/akbar/meritgiving/merit_api.py
```

If it exists, we're done. If not, we need to create it.

- [ ] **Step 2: If claim_update doesn't exist, create it**

Add to `merit_api.py` (after the `claim_verify()` function):

```python
@app.route('/api/claim/update', methods=['POST'])
def claim_update():
    """Update claimed org profile (mission, description, cause tags, donate link)."""
    data = request.get_json(silent=True) or {}
    ein = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]

    if not ein or not token:
        return jsonify({"error": "EIN and verification token required"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM org_claims WHERE ein = ?", (ein,)).fetchone()

    if not row:
        return jsonify({"error": "No claim found for this EIN"}), 404

    # Verify token matches (compare hash)
    if token != row['pin']:  # or implement HMAC comparison if using hashed tokens
        return jsonify({"error": "Verification token invalid"}), 403

    # Update the org with custom fields
    custom_mission = (data.get('custom_mission') or '').strip()[:300]
    custom_description = (data.get('custom_description') or '').strip()[:500]
    cause_tags_json = (data.get('cause_tags_json') or '[]').strip()
    donate_confirmed = data.get('donate_confirmed', False)

    try:
        db.execute(
            """UPDATE registry_enriched SET
               custom_mission = ?,
               custom_description = ?,
               cause_tags = ?,
               donate_confirmed = ?
               WHERE EIN = ?""",
            (custom_mission, custom_description, cause_tags_json, donate_confirmed, ein)
        )
        db.execute(
            "UPDATE org_claims SET claim_status = 'verified', verified_at = datetime('now') WHERE ein = ?",
            (ein,)
        )
        db.commit()
        return jsonify({"success": True, "message": "Profile updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Update failed: {str(e)[:100]}"}), 500
```

- [ ] **Step 3: Commit if added**

```bash
cd /home/akbar/meritgiving
git add merit_api.py
git commit -m "feat: add /api/claim/update endpoint for profile customization"
```

---

## Task 8: End-to-end flow test (manual)

**Manual test of the complete claiming flow.**

- [ ] **Step 1: Start the API**

```bash
cd /home/akbar/meritgiving
source ~/meritgiving/venv/bin/activate
python3 merit_api.py
```

Should print: `Running on http://127.0.0.1:5000`

- [ ] **Step 2: Start the frontend dev server (new terminal)**

```bash
cd /home/akbar/meritgiving/frontend
npm run dev
```

Should print: `http://localhost:5173`

- [ ] **Step 3: Test the flow**

Open `http://localhost:5173/for-nonprofits`:

1. Scroll to the "Claim your page free" button
2. Try to claim with a known EIN (e.g., `52-1231983` from earlier)
3. Enter a test email
4. Should be redirected to `/claim/verify?ein=...&email=...`
5. Enter a PIN (check the API logs or database to see what PIN was set)
6. Should be redirected to `/claim/edit?ein=...&token=...`
7. Fill out mission, description, tags
8. Click "Save profile"
9. Should be redirected to `/claim/success?ein=...`

- [ ] **Step 4: Verify database changes**

```bash
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT EIN, custom_mission, custom_description FROM registry_enriched WHERE EIN = '521231983' LIMIT 1;"
```

Should show your custom mission and description.

- [ ] **Step 5: Check org_claims table**

```bash
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT EIN, claim_status, verified_at FROM org_claims WHERE EIN = '521231983' LIMIT 1;"
```

Should show `claim_status = 'verified'` and a timestamp.

---

## Task 9: Add "Claim your org" link to the home page or header

**Files:**
- Modify: `frontend/src/components/Header.tsx` or `frontend/src/pages/Home.tsx`

Make the claiming flow discoverable by adding a link.

- [ ] **Step 1: Decide placement**

Either:
- **Option A:** Add "For Nonprofits" link to the header nav
- **Option B:** Add a CTA section on the home page

Recommendation: **Option A** — add to the header for consistent discoverability.

- [ ] **Step 2: Find Header.tsx**

```bash
find /home/akbar/meritgiving/frontend/src -name "Header.tsx"
```

- [ ] **Step 3: Add the nav link**

In Header.tsx, find the nav menu items and add:

```typescript
<Link to="/for-nonprofits" className="...nav-link-classes...">
  For Nonprofits
</Link>
```

Or in Home.tsx, add a CTA section before the footer.

- [ ] **Step 4: Test the link**

Visit `http://localhost:5173` and verify the link is visible and clickable.

- [ ] **Step 5: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/src/components/Header.tsx  # or Home.tsx
git commit -m "feat: add For Nonprofits link to header navigation"
```

---

## Task 10: Final verification and cleanup

**Files:**
- Review: All new files

- [ ] **Step 1: Build for production**

```bash
cd /home/akbar/meritgiving/frontend
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 2: Check for any lingering console errors**

```bash
# Re-run the dev server and check browser console
npm run dev
```

Open browser dev tools (F12) and verify no errors on each page:
- `/for-nonprofits`
- `/claim/verify?ein=521231983&email=test@example.com`
- `/claim/edit?ein=521231983&token=xyz`
- `/claim/success?ein=521231983`

- [ ] **Step 3: Final commit**

```bash
cd /home/akbar/meritgiving
git log --oneline | head -10  # Verify all tasks were committed
```

Expected: 10+ commits related to claiming flow.

---

## Verification Checklist

**Before marking complete:**

- [ ] All 5 new pages compile without TypeScript errors
- [ ] API endpoints (`/api/claim/start`, `/api/claim/verify`, `/api/claim/update`) tested manually
- [ ] Full flow works: email → PIN → edit → success
- [ ] Database updates correctly (org_claims.claim_status = 'verified')
- [ ] Links discoverable from header or home page
- [ ] No console errors in browser

---

## Summary

This plan builds a complete nonprofit claiming flow across 10 tasks:

1. **useClaimFlow hook** — Shared state + API calls
2. **ClaimProgressBar** — Visual progress indicator
3. **ClaimVerify** — PIN entry + verification
4. **OrgClaimEditor** — Profile customization (mission, tags, donation link)
5. **ClaimSuccess** — Confirmation page
6. **ForNonprofits routing** — Navigate to verification after email
7. **API verification** — Ensure endpoints exist
8. **Manual end-to-end test** — Validate full flow
9. **Header navigation** — Add discoverability link
10. **Final verification** — Build + browser tests

All changes are isolated, testable, and commit-friendly. The flow integrates with existing backend infrastructure without requiring additional API work.
