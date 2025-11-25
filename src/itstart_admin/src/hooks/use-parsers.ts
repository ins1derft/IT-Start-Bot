import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import type { ParserRead, ParserType } from "@/types/api"
import { useToast } from "@/components/ui/use-toast"

export function useParsers() {
  return useQuery({
    queryKey: ["parsers"],
    queryFn: async () => {
      const response = await api.get("admin/parsers").json<ParserRead[]>()
      return response
    },
  })
}

export function useCreateParser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: {
      source_name: string
      executable_file_path: string
      type: ParserType
      parsing_interval: number
      parsing_start_time: string
      is_active?: boolean
    }) => {
      const searchParams = new URLSearchParams()
      searchParams.set("source_name", data.source_name)
      searchParams.set("executable_file_path", data.executable_file_path)
      searchParams.set("type", data.type)
      searchParams.set("parsing_interval", String(data.parsing_interval))
      searchParams.set("parsing_start_time", data.parsing_start_time)
      if (data.is_active !== undefined) {
        searchParams.set("is_active", String(data.is_active))
      }

      const response = await api
        .post("admin/parsers", {
          searchParams: searchParams.toString(),
        })
        .json<ParserRead>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["parsers"] })
      toast({
        title: "Парсер создан",
        description: "Парсер успешно создан",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось создать парсер",
        variant: "destructive",
      })
    },
  })
}

export function useUpdateParser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: {
      parserId: string
      source_name?: string | null
      executable_file_path?: string | null
      type?: ParserType | null
      parsing_interval?: number | null
      parsing_start_time?: string | null
      is_active?: boolean | null
    }) => {
      const { parserId, ...params } = data
      const searchParams = new URLSearchParams()
      if (params.source_name !== undefined) {
        searchParams.set("source_name", params.source_name || "")
      }
      if (params.executable_file_path !== undefined) {
        searchParams.set(
          "executable_file_path",
          params.executable_file_path || ""
        )
      }
      if (params.type !== undefined) {
        searchParams.set("type", params.type || "")
      }
      if (params.parsing_interval !== undefined) {
        searchParams.set(
          "parsing_interval",
          String(params.parsing_interval || "")
        )
      }
      if (params.parsing_start_time !== undefined) {
        searchParams.set("parsing_start_time", params.parsing_start_time || "")
      }
      if (params.is_active !== undefined) {
        searchParams.set("is_active", String(params.is_active))
      }

      const response = await api
        .patch(`admin/parsers/${parserId}`, {
          searchParams: searchParams.toString(),
        })
        .json<ParserRead>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["parsers"] })
      toast({
        title: "Парсер обновлен",
        description: "Парсер успешно обновлен",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось обновить парсер",
        variant: "destructive",
      })
    },
  })
}

export function useEnableParser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (parserId: string) => {
      await api.post(`admin/parsers/${parserId}/enable`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["parsers"] })
      toast({
        title: "Парсер включен",
        description: "Парсер успешно включен",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось включить парсер",
        variant: "destructive",
      })
    },
  })
}

export function useDisableParser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (parserId: string) => {
      await api.post(`admin/parsers/${parserId}/disable`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["parsers"] })
      toast({
        title: "Парсер отключен",
        description: "Парсер успешно отключен",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось отключить парсер",
        variant: "destructive",
      })
    },
  })
}

