import { useQuery } from "@tanstack/react-query"
import api from "@/lib/api"

interface StatsFilters {
  date_from?: string | Date | null
  date_to?: string | Date | null
  limit?: number
}

export function useUsersStats(filters?: StatsFilters) {
  return useQuery({
    queryKey: ["stats", "users", filters],
    queryFn: async () => {
      const searchParams = new URLSearchParams()
      if (filters?.date_from) {
        const dateStr = filters.date_from instanceof Date
          ? filters.date_from.toISOString().split("T")[0]
          : filters.date_from
        searchParams.set("date_from", dateStr)
      }
      if (filters?.date_to) {
        const dateStr = filters.date_to instanceof Date
          ? filters.date_to.toISOString().split("T")[0]
          : filters.date_to
        searchParams.set("date_to", dateStr)
      }
      const response = await api
        .get("admin/stats/users", {
          searchParams: searchParams.toString(),
        })
        .json<any>()
      return response
    },
  })
}

export function useTagsTop(limit: number = 5) {
  return useQuery({
    queryKey: ["stats", "tags", "top", limit],
    queryFn: async () => {
      const response = await api
        .get("admin/stats/tags/top", {
          searchParams: { limit: String(limit) },
        })
        .json<any>()
      return response
    },
  })
}

export function useParsersErrorPercent(filters?: StatsFilters) {
  return useQuery({
    queryKey: ["stats", "parsers", filters],
    queryFn: async () => {
      const searchParams = new URLSearchParams()
      if (filters?.date_from) {
        const dateStr = filters.date_from instanceof Date
          ? filters.date_from.toISOString().split("T")[0]
          : filters.date_from
        searchParams.set("date_from", dateStr)
      }
      if (filters?.date_to) {
        const dateStr = filters.date_to instanceof Date
          ? filters.date_to.toISOString().split("T")[0]
          : filters.date_to
        searchParams.set("date_to", dateStr)
      }
      const response = await api
        .get("admin/stats/parsers", {
          searchParams: searchParams.toString(),
        })
        .json<any>()
      return response
    },
  })
}

export function usePublicationsPerDay(filters?: StatsFilters) {
  return useQuery({
    queryKey: ["stats", "publications", filters],
    queryFn: async () => {
      const searchParams = new URLSearchParams()
      if (filters?.date_from) {
        const dateStr = filters.date_from instanceof Date
          ? filters.date_from.toISOString().split("T")[0]
          : filters.date_from
        searchParams.set("date_from", dateStr)
      }
      if (filters?.date_to) {
        const dateStr = filters.date_to instanceof Date
          ? filters.date_to.toISOString().split("T")[0]
          : filters.date_to
        searchParams.set("date_to", dateStr)
      }
      const response = await api
        .get("admin/stats/publications", {
          searchParams: searchParams.toString(),
        })
        .json<any>()
      return response
    },
  })
}

