import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  GoogleAuthProvider,
  isSignInWithEmailLink,
  onAuthStateChanged,
  sendSignInLinkToEmail,
  signInWithEmailLink,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth'
import { auth } from '../lib/firebase'

const ACTION_CODE_SETTINGS = {
  url: `${window.location.origin}/wallet?emailSignIn=1`,
  handleCodeInApp: true,
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  sendMagicLink: (email: string) => Promise<void>
  signOut: () => Promise<void>
  getIdToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, u => {
      setUser(u)
      setLoading(false)
    })
    return unsub
  }, [])

  // Complete email magic-link sign-in if we landed back from the link
  useEffect(() => {
    if (isSignInWithEmailLink(auth, window.location.href)) {
      const email = window.localStorage.getItem('daanaa_signin_email')
      if (email) {
        signInWithEmailLink(auth, email, window.location.href)
          .then(() => window.localStorage.removeItem('daanaa_signin_email'))
          .catch(console.error)
      }
    }
  }, [])

  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider()
    provider.addScope('email')
    provider.addScope('profile')
    try {
      await signInWithPopup(auth, provider)
    } catch (error: any) {
      console.error('Google sign-in error:', error.code, error.message)
      // Re-throw with user-friendly message
      if (error.code === 'auth/popup-blocked') {
        throw new Error('Sign-in popup was blocked. Please allow popups and try again.')
      } else if (error.code === 'auth/popup-closed-by-user') {
        throw new Error('Sign-in was cancelled.')
      } else if (error.code === 'auth/network-request-failed') {
        throw new Error('Network error. Please check your internet connection.')
      }
      throw new Error(error.message || 'Failed to sign in with Google')
    }
  }

  const sendMagicLink = async (email: string) => {
    await sendSignInLinkToEmail(auth, email, ACTION_CODE_SETTINGS)
    window.localStorage.setItem('daanaa_signin_email', email)
  }

  const signOut = async () => {
    await firebaseSignOut(auth)
  }

  const getIdToken = async (): Promise<string | null> => {
    if (!user) return null
    return user.getIdToken()
  }

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, sendMagicLink, signOut, getIdToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
