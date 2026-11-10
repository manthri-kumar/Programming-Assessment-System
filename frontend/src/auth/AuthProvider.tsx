import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Role, User } from '../api/types'
import { session } from './session'

interface AuthState { user: User | null; loading: boolean; notice: string | null; login(email: string, password: string): Promise<User>; register(email: string, password: string, role: Role, code?: string): Promise<void>; logout(): void }
const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(session.user())
  const [loading, setLoading] = useState(Boolean(session.token()))
  const [notice, setNotice] = useState<string | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!session.token()) return
    api.me().then(value => { session.setUser(value); setUser(value) }).catch(() => { session.clear(); setUser(null) }).finally(() => setLoading(false))
  }, [])
  useEffect(() => {
    const expired = () => { queryClient.clear(); setUser(null); setNotice('Your session expired. Please sign in again.') }
    window.addEventListener('codeassess:session-expired', expired)
    return () => window.removeEventListener('codeassess:session-expired', expired)
  }, [queryClient])

  const value = useMemo<AuthState>(() => ({
    user, loading, notice,
    async login(email, password) { const token = await api.login(email, password); session.setToken(token.access_token); const current = await api.me(); session.setUser(current); setUser(current); setNotice(null); return current },
    async register(email, password, role, code) { await api.register(email, password, role, code) },
    logout() { session.clear(); queryClient.clear(); setUser(null); setNotice(null) },
  }), [loading, notice, queryClient, user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider is missing'); return value }
