import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useCreateUser } from "@/hooks/use-admin-users"
import { createUserSchema } from "@/lib/schemas"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/use-toast"
import type { AdminUserCreateResponse } from "@/types/api"
import type { z } from "zod"

type CreateUserFormValues = z.infer<typeof createUserSchema>

interface CreateUserDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreateUserDialog({
  open,
  onOpenChange,
}: CreateUserDialogProps) {
  const createUserMutation = useCreateUser()
  const { toast } = useToast()
  const [created, setCreated] = useState<AdminUserCreateResponse | null>(null)

  const form = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      username: "",
      role: "moderator",
    },
  })

  useEffect(() => {
    if (!open) {
      setCreated(null)
      form.reset()
    }
  }, [open, form])

  const onSubmit = async (data: CreateUserFormValues) => {
    const result = await createUserMutation.mutateAsync(data)
    setCreated(result)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {created ? "Пользователь создан" : "Создать пользователя"}
          </DialogTitle>
          <DialogDescription>
            {created
              ? "Сохраните временный пароль — он больше не будет показан."
              : "Создайте нового пользователя админки"}
          </DialogDescription>
        </DialogHeader>
        {created ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="text-sm text-muted-foreground">
                Пользователь: <span className="font-medium text-foreground">{created.user.username}</span>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Временный пароль</div>
                <div className="flex gap-2">
                  <Input readOnly value={created.temporary_password} />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(created.temporary_password)
                        toast({
                          title: "Скопировано",
                          description: "Временный пароль скопирован в буфер обмена",
                        })
                      } catch {
                        toast({
                          title: "Не удалось скопировать",
                          description: "Скопируйте пароль вручную",
                          variant: "destructive",
                        })
                      }
                    }}
                  >
                    Копировать
                  </Button>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" onClick={() => onOpenChange(false)}>
                Готово
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Имя пользователя</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Роль</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Выберите роль" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="admin">Администратор</SelectItem>
                        <SelectItem value="moderator">Модератор</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  disabled={createUserMutation.isPending}
                >
                  {createUserMutation.isPending ? "Создание..." : "Создать"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  )
}
