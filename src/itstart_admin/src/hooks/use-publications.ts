import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import type {
  PublicationRead,
  PublicationType,
} from "@/types/api"
import { useToast } from "@/components/ui/use-toast"

interface PublicationsFilters {
  pub_type?: PublicationType | null
  status?: string | null
  date_from?: string | Date | null
  date_to?: string | Date | null
  tag_ids?: string[] | null
}

export function usePublications(filters?: PublicationsFilters) {
  return useQuery({
    queryKey: ["publications", filters],
    queryFn: async () => {
      const searchParams = new URLSearchParams()
      if (filters?.pub_type) {
        searchParams.set("pub_type", filters.pub_type)
      }
      if (filters?.status) {
        searchParams.set("status", filters.status)
      }
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

      const options: any = {
        searchParams: searchParams.toString(),
      }

      // Tag IDs should be sent in request body according to OpenAPI spec
      if (filters?.tag_ids && filters.tag_ids.length > 0) {
        options.json = filters.tag_ids
      }

      const response = await api
        .get("admin/publications", options)
        .json<PublicationRead[]>()
      return response
    },
  })
}

export function usePublication(id: string) {
  return useQuery({
    queryKey: ["publication", id],
    queryFn: async () => {
      const response = await api
        .get(`admin/publications/${id}`)
        .json<PublicationRead>()
      return response
    },
    enabled: !!id,
  })
}

export function useUpdatePublication() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: {
      pubId: string
      title?: string | null
      description?: string | null
      status?: string | null
      contact_info?: string | null
      deadline_at?: string | null
    }) => {
      const { pubId, ...params } = data
      const searchParams = new URLSearchParams()
      if (params.title !== undefined) {
        searchParams.set("title", params.title || "")
      }
      if (params.description !== undefined) {
        searchParams.set("description", params.description || "")
      }
      if (params.status !== undefined) {
        searchParams.set("status", params.status || "")
      }
      if (params.contact_info !== undefined) {
        searchParams.set("contact_info", params.contact_info || "")
      }
      if (params.deadline_at !== undefined) {
        searchParams.set("deadline_at", params.deadline_at || "")
      }

      const response = await api
        .patch(`admin/publications/${pubId}`, {
          searchParams: searchParams.toString(),
        })
        .json<PublicationRead>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["publications"] })
      toast({
        title: "Публикация обновлена",
        description: "Публикация успешно обновлена",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось обновить публикацию",
        variant: "destructive",
      })
    },
  })
}

export function useDeclinePublication() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: { pubId: string; reason: string }) => {
      await api.post(`admin/publications/${data.pubId}/decline`, {
        searchParams: { reason: data.reason },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["publications"] })
      toast({
        title: "Публикация отклонена",
        description: "Публикация успешно отклонена",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось отклонить публикацию",
        variant: "destructive",
      })
    },
  })
}

export function useApproveAndSend() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (pubId: string) => {
      await api.post(`admin/publications/${pubId}/approve-and-send`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["publications"] })
      toast({
        title: "Публикация одобрена и отправлена",
        description: "Публикация успешно одобрена и отправлена",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description:
          error?.message || "Не удалось одобрить и отправить публикацию",
        variant: "destructive",
      })
    },
  })
}

