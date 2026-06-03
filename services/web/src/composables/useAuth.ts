export const DEFAULT_CREDENTIALS = { username: 'admin', password: 'admin' } as const

const STORAGE_KEY = 'atlas_auth'

export interface AuthSession {
  username: string
  loggedInAt: string
}

function readSession(): AuthSession | null {
  const raw = localStorage.getItem(STORAGE_KEY) || sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthSession
  } catch {
    return null
  }
}

export function isAuthenticated(): boolean {
  return readSession() !== null
}

export function getCurrentUser(): string | null {
  return readSession()?.username ?? null
}

export function login(username: string, password: string, remember: boolean): boolean {
  if (username !== DEFAULT_CREDENTIALS.username || password !== DEFAULT_CREDENTIALS.password) {
    return false
  }
  clearAuth()
  const session: AuthSession = { username, loggedInAt: new Date().toISOString() }
  const storage = remember ? localStorage : sessionStorage
  storage.setItem(STORAGE_KEY, JSON.stringify(session))
  return true
}

export function clearAuth(): void {
  localStorage.removeItem(STORAGE_KEY)
  sessionStorage.removeItem(STORAGE_KEY)
}
