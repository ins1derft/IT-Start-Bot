import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useLogin } from "@/hooks/use-auth"
import { loginSchema } from "@/lib/schemas"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import type { z } from "zod"

type LoginFormValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const loginMutation = useLogin()

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
      otp_code: null,
    },
  })

  const onSubmit = async (data: LoginFormValues) => {
    await loginMutation.mutateAsync(data)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Вход в админку</CardTitle>
          <CardDescription>
            Введите ваши учетные данные для входа
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                form.handleSubmit(onSubmit)(e)
              }}
              className="space-y-4"
            >
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Имя пользователя</FormLabel>
                    <FormControl>
                      <Input {...field} autoComplete="username" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Пароль</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="password"
                        autoComplete="current-password"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="otp_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Код 2FA (если настроен)</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value || ""}
                        placeholder="000000"
                        maxLength={6}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button
                type="submit"
                className="w-full"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending ? "Вход..." : "Войти"}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}

