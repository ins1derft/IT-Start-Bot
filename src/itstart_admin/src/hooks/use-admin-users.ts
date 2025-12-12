import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import type { AdminUserRead, AdminRole, AdminUserCreateResponse } from "@/types/api"
import { useToast } from "@/components/ui/use-toast"

export function useUsers() {
  return useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const response = await api.get("admin/users").json<AdminUserRead[]>()
      return response
    },
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: {
      username: string
      role: AdminRole
    }) => {
      const response = await api
        .post("admin/users", {
          searchParams: data,
        })
        .json<AdminUserCreateResponse>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      toast({
        title: "Пользователь создан",
        description: "Временный пароль показан в окне создания",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось создать пользователя",
        variant: "destructive",
      })
    },
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: {
      userId: string
      role?: AdminRole
      is_active?: boolean
      password?: string | null
    }) => {
      const { userId, ...params } = data
      const searchParams = new URLSearchParams()
      if (params.role !== undefined) {
        searchParams.set("role", params.role)
      }
      if (params.is_active !== undefined) {
        searchParams.set("is_active", String(params.is_active))
      }
      if (params.password !== undefined && params.password !== null) {
        searchParams.set("password", params.password)
      }

      const response = await api
        .patch(`admin/users/${userId}`, {
          searchParams: searchParams.toString(),
        })
        .json<AdminUserRead>()
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      toast({
        title: "Пользователь обновлен",
        description: "Данные пользователя успешно обновлены",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось обновить пользователя",
        variant: "destructive",
      })
    },
  })
}

export function useDisableUser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`admin/users/${userId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      toast({
        title: "Пользователь отключен",
        description: "Пользователь успешно отключен",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось отключить пользователя",
        variant: "destructive",
      })
    },
  })
}
