import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import api from "@/lib/api"
import {
  setTokens,
  clearTokens,
  setUser,
} from "@/lib/auth"
import type {
  TokenResponse,
  LoginRequest,
  ChangePasswordRequest,
  TOTPSetupResponse,
  OTPCode,
  AdminUserRead,
} from "@/types/api"
import { useToast } from "@/components/ui/use-toast"

export function useLogin() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const response = await api
        .post("auth/login", { json: data })
        .json<TokenResponse>()
      return response
    },
    onSuccess: async (data) => {
      setTokens(data)

      try {
        const me = await api.get("auth/me").json<AdminUserRead>()
        setUser({ username: me.username, role: me.role })
      } catch (error) {
        clearTokens()
        toast({
          title: "Ошибка",
          description: "Не удалось получить данные пользователя после входа",
          variant: "destructive",
        })
        return
      }

      queryClient.invalidateQueries()
      navigate("/")
      toast({
        title: "Успешный вход",
        description: "Вы успешно вошли в систему",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка входа",
        description: error?.message || "Неверные учетные данные",
        variant: "destructive",
      })
    },
  })
}

export function useRefreshToken() {
  return useMutation({
    mutationFn: async () => {
      const response = await api
        .post("auth/refresh")
        .json<TokenResponse>()
      return response
    },
    onSuccess: (data) => {
      setTokens(data)
    },
  })
}

export function useChangePassword() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: ChangePasswordRequest) => {
      await api.post("auth/change-password", { json: data })
    },
    onSuccess: () => {
      toast({
        title: "Пароль изменен",
        description: "Пароль успешно изменен",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось изменить пароль",
        variant: "destructive",
      })
    },
  })
}

export function useSetup2FA() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: async () => {
      const response = await api
        .post("auth/setup-2fa")
        .json<TOTPSetupResponse>()
      return response
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось настроить 2FA",
        variant: "destructive",
      })
    },
  })
}

export function useConfirm2FA() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: OTPCode) => {
      await api.post("auth/confirm-2fa", { json: data })
    },
    onSuccess: () => {
      toast({
        title: "2FA подтверждена",
        description: "Двухфакторная аутентификация успешно настроена",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Неверный код",
        variant: "destructive",
      })
    },
  })
}

export function useDisable2FA() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: OTPCode) => {
      await api.delete("auth/disable-2fa", { json: data })
    },
    onSuccess: () => {
      toast({
        title: "2FA отключена",
        description: "Двухфакторная аутентификация отключена",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось отключить 2FA",
        variant: "destructive",
      })
    },
  })
}

export function useLogout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return () => {
    clearTokens()
    queryClient.clear()
    navigate("/login")
  }
}
