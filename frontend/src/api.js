export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

export async function request(path, options = {}) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 45000)
  try {
    const token = localStorage.getItem('construction_access_token')
    const headers = new Headers(options.headers || {})
    if (token) headers.set('Authorization', `Bearer ${token}`)
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers, signal: controller.signal })
    const body = await response.json().catch(() => null)
    if (!response.ok) {
      const detail = body?.detail
      throw new Error(typeof detail === 'string' ? detail : 'The request was rejected. Check the image and site context, then try again.')
    }
    if (!body && response.status !== 204) throw new Error('The server returned an unexpected response. Please try again.')
    return body
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request timed out. Refresh history before retrying; the image may have been saved.')
    if (error instanceof TypeError) throw new Error('Cannot reach the API. Start the backend and check VITE_API_BASE_URL. Refresh history before retrying an upload.')
    throw error
  } finally {
    clearTimeout(timeout)
  }
}

export async function fetchImage(path) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 45000)
  try {
    const token = localStorage.getItem('construction_access_token')
    const headers = new Headers()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    const response = await fetch(`${API_BASE}${path}`, { headers, signal: controller.signal })
    if (!response.ok) throw new Error('The saved image could not be loaded.')
    return URL.createObjectURL(await response.blob())
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The saved image request timed out.')
    if (error instanceof TypeError) throw new Error('Cannot reach the API while loading the saved image.')
    throw error
  } finally {
    clearTimeout(timeout)
  }
}

export function saveAuthToken(token) {
  localStorage.setItem('construction_access_token', token)
}

export function clearAuthToken() {
  localStorage.removeItem('construction_access_token')
}

export const projectRequest = (path, options = {}) => request(`/api/projects${path}`, options)
