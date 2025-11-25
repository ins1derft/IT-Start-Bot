import ky from "ky"
import type { TokenResponse } from "@/types/api"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

// Create base API client
const api = ky.create({
  prefixUrl: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  hooks: {
    beforeRequest: [
      (request) => {
        const token = localStorage.getItem("access_token")
        if (token) {
          request.headers.set("Authorization", `Bearer ${token}`)
        }
      },
    ],
    afterResponse: [
      async (request, _options, response) => {
        if (response.status === 401) {
          // Try to refresh token
          const refreshToken = localStorage.getItem("refresh_token")
          if (refreshToken) {
            try {
              const newTokens = await ky
                .post(`${API_URL}/auth/refresh`, {
                  headers: {
                    Authorization: `Bearer ${refreshToken}`,
                  },
                })
                .json<TokenResponse>()

              localStorage.setItem("access_token", newTokens.access_token)
              localStorage.setItem("refresh_token", newTokens.refresh_token)

              // Retry original request
              request.headers.set(
                "Authorization",
                `Bearer ${newTokens.access_token}`
              )
              return ky(request)
            } catch (error) {
              // Refresh failed, clear tokens and redirect to login
              localStorage.removeItem("access_token")
              localStorage.removeItem("refresh_token")
              window.location.href = "/login"
              throw error
            }
          } else {
            // No refresh token, redirect to login
            localStorage.removeItem("access_token")
            window.location.href = "/login"
          }
        }
        return response
      },
    ],
  },
})

export default api

