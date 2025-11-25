import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import type { TagRead, TagCategory } from "@/types/api"
import { useToast } from "@/components/ui/use-toast"

export function useTags(category?: TagCategory | null) {
  return useQuery({
    queryKey: ["tags", category],
    queryFn: async () => {
      const searchParams = new URLSearchParams()
      if (category) {
        searchParams.set("category", category)
      }
      const response = await api
        .get("admin/tags", {
          searchParams: searchParams.toString(),
        })
        .json<TagRead[]>()
      return response
    },
  })
}

export function useCreateTag() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: { name: string; category: TagCategory }) => {
      const response = await api
        .post("admin/tags", {
          searchParams: data,
        })
        .json<TagRead>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] })
      toast({
        title: "Тег создан",
        description: "Тег успешно создан",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось создать тег",
        variant: "destructive",
      })
    },
  })
}

export function useUpdateTag() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: {
      tagId: string
      name: string
      category: TagCategory
    }) => {
      const { tagId, ...params } = data
      const response = await api
        .patch(`admin/tags/${tagId}`, {
          searchParams: params,
        })
        .json<TagRead>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] })
      toast({
        title: "Тег обновлен",
        description: "Тег успешно обновлен",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось обновить тег",
        variant: "destructive",
      })
    },
  })
}

export function useDeleteTag() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (tagId: string) => {
      await api.delete(`admin/tags/${tagId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] })
      toast({
        title: "Тег удален",
        description: "Тег успешно удален",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось удалить тег",
        variant: "destructive",
      })
    },
  })
}

