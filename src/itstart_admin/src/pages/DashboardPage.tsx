import { Navigate } from "react-router-dom"
import { getUser } from "@/lib/auth"

export function DashboardPage() {
  const user = getUser()

  // Redirect based on role
  if (user?.role === "admin") {
    return <Navigate to="/publications" replace />
  }

  return <Navigate to="/publications" replace />
}

