import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import type {
  PublicationScheduleRead,
  PublicationScheduleUpdate,
} from "@/types/api"
import { useToast } from "@/components/ui/use-toast"

export function usePublicationSchedule() {
  return useQuery({
    queryKey: ["schedule", "publications"],
    queryFn: async () => {
      const response = await api
        .get("admin/schedule/publications")
        .json<PublicationScheduleRead[]>()
      return response
    },
  })
}

export function useUpdateSchedule() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: PublicationScheduleUpdate) => {
      const response = await api
        .patch("admin/schedule/publications", {
          json: data,
        })
        .json<PublicationScheduleRead[]>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule"] })
      toast({
        title: "Расписание обновлено",
        description: "Расписание успешно обновлено",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось обновить расписание",
        variant: "destructive",
      })
    },
  })
}

