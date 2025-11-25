import { useState } from "react"
import { useLogout, useChangePassword, useDisable2FA, useSetup2FA, useConfirm2FA } from "@/hooks/use-auth"
import { getUser } from "@/lib/auth"
import { formatRole } from "@/lib/format"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { changePasswordSchema, otpCodeSchema } from "@/lib/schemas"
import { TwoFASetup } from "@/components/auth/TwoFASetup"
import { FiUser, FiLogOut, FiKey, FiShield, FiShieldOff } from "react-icons/fi"
import type { z } from "zod"

type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>
type OTPFormValues = z.infer<typeof otpCodeSchema>

export function Header() {
  const user = getUser()
  const logout = useLogout()
  const changePasswordMutation = useChangePassword()
  const disable2FAMutation = useDisable2FA()
  const setup2FAMutation = useSetup2FA()
  const confirm2FAMutation = useConfirm2FA()
  const [showChangePassword, setShowChangePassword] = useState(false)
  const [showDisable2FA, setShowDisable2FA] = useState(false)
  const [showSetup2FA, setShowSetup2FA] = useState(false)
  const [twoFASecret, setTwoFASecret] = useState<string | null>(null)

  const changePasswordForm = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      old_password: "",
      new_password: "",
    },
  })

  const disable2FAForm = useForm<OTPFormValues>({
    resolver: zodResolver(otpCodeSchema),
    defaultValues: {
      code: "",
    },
  })

  const handleChangePassword = async (data: ChangePasswordFormValues) => {
    await changePasswordMutation.mutateAsync(data)
    setShowChangePassword(false)
    changePasswordForm.reset()
  }

  const handleDisable2FA = async (data: OTPFormValues) => {
    await disable2FAMutation.mutateAsync(data)
    setShowDisable2FA(false)
    disable2FAForm.reset()
  }

  const handleSetup2FA = async () => {
    try {
      const result = await setup2FAMutation.mutateAsync()
      setTwoFASecret(result.secret)
      setShowSetup2FA(true)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleConfirm2FA = async (code: string) => {
    try {
      await confirm2FAMutation.mutateAsync({ code })
      setShowSetup2FA(false)
      setTwoFASecret(null)
    } catch (error) {
      // Error handled by mutation
    }
  }

  if (!user) return null

  return (
    <>
      <header className="flex h-16 items-center justify-between border-b bg-background px-6">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">Админ-панель</h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            {formatRole(user.role as any)}
          </span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2">
                <FiUser className="h-4 w-4" />
                <span>{user.username}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Мой аккаунт</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setShowChangePassword(true)}>
                <FiKey className="mr-2 h-4 w-4" />
                Сменить пароль
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleSetup2FA}>
                <FiShield className="mr-2 h-4 w-4" />
                Настроить 2FA
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setShowDisable2FA(true)}>
                <FiShieldOff className="mr-2 h-4 w-4" />
                Отключить 2FA
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <FiLogOut className="mr-2 h-4 w-4" />
                Выйти
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <Dialog open={showChangePassword} onOpenChange={setShowChangePassword}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Смена пароля</DialogTitle>
            <DialogDescription>
              Введите текущий пароль и новый пароль
            </DialogDescription>
          </DialogHeader>
          <Form {...changePasswordForm}>
            <form
              onSubmit={changePasswordForm.handleSubmit(handleChangePassword)}
              className="space-y-4"
            >
              <FormField
                control={changePasswordForm.control}
                name="old_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Текущий пароль</FormLabel>
                    <FormControl>
                      <Input {...field} type="password" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={changePasswordForm.control}
                name="new_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Новый пароль</FormLabel>
                    <FormControl>
                      <Input {...field} type="password" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowChangePassword(false)}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  disabled={changePasswordMutation.isPending}
                >
                  {changePasswordMutation.isPending
                    ? "Сохранение..."
                    : "Сохранить"}
                </Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog open={showDisable2FA} onOpenChange={setShowDisable2FA}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Отключение 2FA</DialogTitle>
            <DialogDescription>
              Введите код из приложения-аутентификатора для подтверждения
            </DialogDescription>
          </DialogHeader>
          <Form {...disable2FAForm}>
            <form
              onSubmit={disable2FAForm.handleSubmit(handleDisable2FA)}
              className="space-y-4"
            >
              <FormField
                control={disable2FAForm.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Код подтверждения</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="000000"
                        maxLength={6}
                        className="text-center text-2xl tracking-widest"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowDisable2FA(false)}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  disabled={disable2FAMutation.isPending}
                >
                  {disable2FAMutation.isPending
                    ? "Отключение..."
                    : "Отключить"}
                </Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {showSetup2FA && twoFASecret && (
        <Dialog open={showSetup2FA} onOpenChange={setShowSetup2FA}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Настройка 2FA</DialogTitle>
              <DialogDescription>
                Отсканируйте QR код в приложении-аутентификаторе и введите код
                подтверждения
              </DialogDescription>
            </DialogHeader>
            <TwoFASetup
              secret={twoFASecret}
              onConfirm={handleConfirm2FA}
              onCancel={() => {
                setShowSetup2FA(false)
                setTwoFASecret(null)
              }}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}

