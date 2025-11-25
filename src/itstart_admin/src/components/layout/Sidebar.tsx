import { Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"
import { getUser } from "@/lib/auth"
import {
  FiFileText,
  FiUsers,
  FiTag,
  FiDatabase,
  FiBarChart,
  FiCalendar,
  FiLayout,
} from "react-icons/fi"
import type { AdminRole } from "@/types/api"

interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  roles: AdminRole[]
}

const navItems: NavItem[] = [
  {
    title: "Публикации",
    href: "/publications",
    icon: FiFileText,
    roles: ["admin", "moderator"],
  },
  {
    title: "Пользователи",
    href: "/admin/users",
    icon: FiUsers,
    roles: ["admin"],
  },
  {
    title: "Теги",
    href: "/admin/tags",
    icon: FiTag,
    roles: ["admin"],
  },
  {
    title: "Парсеры",
    href: "/admin/parsers",
    icon: FiDatabase,
    roles: ["admin"],
  },
  {
    title: "Статистика",
    href: "/admin/stats",
    icon: FiBarChart,
    roles: ["admin"],
  },
  {
    title: "Расписание",
    href: "/admin/schedule",
    icon: FiCalendar,
    roles: ["admin"],
  },
]

export function Sidebar() {
  const location = useLocation()
  const user = getUser()

  const filteredItems = navItems.filter((item) =>
    user ? item.roles.includes(user.role as AdminRole) : false
  )

  return (
    <aside className="w-64 border-r bg-background">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center border-b px-6">
          <Link to="/" className="flex items-center gap-2">
            <FiLayout className="h-6 w-6" />
            <span className="text-lg font-semibold">ITStart Admin</span>
          </Link>
        </div>
        <nav className="flex-1 space-y-1 p-4">
          {filteredItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href

            return (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5" />
                {item.title}
              </Link>
            )
          })}
        </nav>
      </div>
    </aside>
  )
}

