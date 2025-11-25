import { Navigate } from "react-router-dom"
import { getUser } from "@/lib/auth"
import type { AdminRole } from "@/types/api"

interface RoleGuardProps {
  children: React.ReactNode
  allowedRoles: AdminRole[]
}

export function RoleGuard({ children, allowedRoles }: RoleGuardProps) {
  const user = getUser()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (!allowedRoles.includes(user.role as AdminRole)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

