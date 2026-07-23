import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'

export interface ProfileContext {
  context_id: string
  context_type: 'household' | 'daf' | 'business' | 'other'
  status: 'active' | 'archived'
  created_by_uid: string
  created_at: string
  role: 'lead' | 'support' | 'member' | 'viewer'
  member_count: number
}

export interface ContextMember {
  firebase_uid: string
  role: 'lead' | 'support' | 'member' | 'viewer'
  status: 'active' | 'removed'
  joined_at: string
  created_at: string
}

export interface PendingInvitation {
  invitation_id: string
  context_id: string
  role: 'lead' | 'support' | 'member' | 'viewer'
  context_type: 'household' | 'daf' | 'business' | 'other'
  invited_by_uid: string
  created_at: string
  expires_at: string
}

export function useProfileContexts() {
  const { getIdToken } = useAuth()
  const [contexts, setContexts] = useState<ProfileContext[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const apiCall = useCallback(async (method: string, path: string, body?: any) => {
    const token = await getIdToken()
    if (!token) throw new Error('Not authenticated')

    const response = await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.error || `API error: ${response.status}`)
    }

    return response.json()
  }, [getIdToken])

  const fetchContexts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiCall('GET', '/api/profile-contexts')
      setContexts(data.contexts || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contexts')
    } finally {
      setLoading(false)
    }
  }, [apiCall])

  const createContext = useCallback(async (contextType: string) => {
    try {
      const data = await apiCall('POST', '/api/profile-contexts', { context_type: contextType })
      setContexts(prev => [...prev, data.context])
      return data.context_id
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to create context')
    }
  }, [apiCall])

  const getMembers = useCallback(async (contextId: string) => {
    const data = await apiCall('GET', `/api/profile-contexts/${contextId}/members`)
    return data.members as ContextMember[]
  }, [apiCall])

  const inviteMember = useCallback(async (contextId: string, firebaseUid: string, role: string) => {
    const data = await apiCall('POST', `/api/profile-contexts/${contextId}/members`, {
      firebase_uid: firebaseUid,
      role,
    })
    return data.invitation_id
  }, [apiCall])

  const updateMemberRole = useCallback(async (contextId: string, firebaseUid: string, newRole: string) => {
    await apiCall('PATCH', `/api/profile-contexts/${contextId}/members/${firebaseUid}`, {
      role: newRole,
    })
  }, [apiCall])

  const removeMember = useCallback(async (contextId: string, firebaseUid: string) => {
    await apiCall('DELETE', `/api/profile-contexts/${contextId}/members/${firebaseUid}`)
  }, [apiCall])

  const getPendingInvitations = useCallback(async () => {
    const data = await apiCall('GET', '/api/profile-contexts/invitations/pending')
    return data.invitations as PendingInvitation[]
  }, [apiCall])

  const acceptInvitation = useCallback(async (invitationId: string) => {
    await apiCall('POST', `/api/profile-contexts/invitations/${invitationId}/accept`)
  }, [apiCall])

  const rejectInvitation = useCallback(async (invitationId: string) => {
    await apiCall('POST', `/api/profile-contexts/invitations/${invitationId}/reject`)
  }, [apiCall])

  const archiveContext = useCallback(async (contextId: string) => {
    await apiCall('POST', `/api/profile-contexts/${contextId}/archive`)
    setContexts(prev => prev.map(c =>
      c.context_id === contextId ? { ...c, status: 'archived' } : c
    ))
  }, [apiCall])

  useEffect(() => {
    fetchContexts()
  }, [fetchContexts])

  return {
    contexts,
    loading,
    error,
    fetchContexts,
    createContext,
    getMembers,
    inviteMember,
    updateMemberRole,
    removeMember,
    getPendingInvitations,
    acceptInvitation,
    rejectInvitation,
    archiveContext,
  }
}
