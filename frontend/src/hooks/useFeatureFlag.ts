import { useState, useEffect } from 'react'

const FEATURE_FLAG_KEY = 'daanaa_feature_flags'

// Deterministic 1% sampling: hash user ID to consistent flag across sessions
function isUserInCohort(userId: string, percentage: number): boolean {
  let hash = 0
  for (let i = 0; i < userId.length; i++) {
    const char = userId.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return (Math.abs(hash) % 100) < percentage
}

export function useFeatureFlag(flagName: string, percentage: number = 1): boolean {
  const [isEnabled, setIsEnabled] = useState<boolean | null>(null)

  useEffect(() => {
    // Generate persistent user ID from localStorage (tracks across sessions)
    let userId = localStorage.getItem('daanaa_user_id')
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('daanaa_user_id', userId)
    }

    // Check if user is in cohort for this feature
    const enabled = isUserInCohort(userId, percentage)
    setIsEnabled(enabled)
  }, [flagName, percentage])

  // Return null while loading (to avoid hydration mismatch)
  return isEnabled === null ? false : isEnabled
}
