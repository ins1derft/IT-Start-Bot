import { createBrowserRouter } from "react-router-dom"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"
import { RoleGuard } from "@/components/auth/RoleGuard"
import { AppLayout } from "@/components/layout/AppLayout"
import { LoginPage } from "@/pages/auth/LoginPage"
import { PublicationsPage } from "@/pages/publications/PublicationsPage"
import { PublicationDetailPage } from "@/pages/publications/PublicationDetailPage"
import { UsersPage } from "@/pages/admin-users/UsersPage"
import { TagsPage } from "@/pages/tags/TagsPage"
import { ParsersPage } from "@/pages/parsers/ParsersPage"
import { StatsPage } from "@/pages/stats/StatsPage"
import { SchedulePage } from "@/pages/schedule/SchedulePage"
import { DashboardPage } from "@/pages/DashboardPage"
import { NotFoundPage } from "@/pages/NotFoundPage"

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout>
          <DashboardPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/publications",
    element: (
      <ProtectedRoute>
        <AppLayout>
          <PublicationsPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/publications/:id",
    element: (
      <ProtectedRoute>
        <AppLayout>
          <PublicationDetailPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/users",
    element: (
      <ProtectedRoute>
        <RoleGuard allowedRoles={["admin"]}>
          <AppLayout>
            <UsersPage />
          </AppLayout>
        </RoleGuard>
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/tags",
    element: (
      <ProtectedRoute>
        <RoleGuard allowedRoles={["admin"]}>
          <AppLayout>
            <TagsPage />
          </AppLayout>
        </RoleGuard>
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/parsers",
    element: (
      <ProtectedRoute>
        <RoleGuard allowedRoles={["admin"]}>
          <AppLayout>
            <ParsersPage />
          </AppLayout>
        </RoleGuard>
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/stats",
    element: (
      <ProtectedRoute>
        <RoleGuard allowedRoles={["admin"]}>
          <AppLayout>
            <StatsPage />
          </AppLayout>
        </RoleGuard>
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/schedule",
    element: (
      <ProtectedRoute>
        <RoleGuard allowedRoles={["admin"]}>
          <AppLayout>
            <SchedulePage />
          </AppLayout>
        </RoleGuard>
      </ProtectedRoute>
    ),
  },
  {
    path: "*",
    element: (
      <ProtectedRoute>
        <AppLayout>
          <NotFoundPage />
        </AppLayout>
      </ProtectedRoute>
    ),
  },
])

