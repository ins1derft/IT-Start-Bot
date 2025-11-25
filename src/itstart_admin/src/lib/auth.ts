import type { TokenResponse } from "@/types/api"

const ACCESS_TOKEN_KEY = "access_token"
const REFRESH_TOKEN_KEY = "refresh_token"
const USER_KEY = "user"

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function isAuthenticated(): boolean {
  return !!getAccessToken()
}

export function setUser(user: { username: string; role: string }): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function getUser(): { username: string; role: string } | null {
  const userStr = localStorage.getItem(USER_KEY)
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

