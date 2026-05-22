const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '')

export const APP_BASE = import.meta.env.VITE_APP_BASE || '/'
export const API_BASE = trimTrailingSlash(import.meta.env.VITE_API_BASE || '/api')
