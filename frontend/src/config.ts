const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '')

export const APP_BASE = import.meta.env.VITE_APP_BASE || '/web/dwgconvert/'
export const API_BASE = trimTrailingSlash(import.meta.env.VITE_API_BASE || '/public/dwgconvert/api')
export const APP_HASH_PREFIX = import.meta.env.VITE_APP_HASH_PREFIX || ''
