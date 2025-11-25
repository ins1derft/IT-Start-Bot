import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { DateTimePicker } from "@/components/ui/date-picker"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useUpdatePublication } from "@/hooks/use-publications"
import type { PublicationRead } from "@/types/api"

const editPublicationSchema = z.object({
  title: z.string().min(1, "Название обязательно"),
  description: z.string().min(1, "Описание обязательно"),
  status: z.string().min(1, "Статус обязателен"),
  contact_info: z.string().optional().nullable(),
  deadline_at: z.date().optional().nullable(),
})

type EditPublicationFormValues = z.infer<typeof editPublicationSchema>

interface EditPublicationDialogProps {
  publication: PublicationRead
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function EditPublicationDialog({
  publication,
  open,
  onOpenChange,
}: EditPublicationDialogProps) {
  const updatePublication = useUpdatePublication()

  const form = useForm<EditPublicationFormValues>({
    resolver: zodResolver(editPublicationSchema),
    defaultValues: {
      title: publication.title,
      description: publication.description,
      status: publication.status,
      contact_info: publication.contact_info || "",
      deadline_at: publication.deadline_at
        ? new Date(publication.deadline_at)
        : null,
    },
  })

  const onSubmit = async (data: EditPublicationFormValues) => {
    await updatePublication.mutateAsync({
      pubId: publication.id,
      title: data.title,
      description: data.description,
      status: data.status,
      contact_info: data.contact_info || null,
      deadline_at: data.deadline_at
        ? data.deadline_at.toISOString()
        : null,
    })
    onOpenChange(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Редактировать публикацию</DialogTitle>
          <DialogDescription>
            Измените данные публикации. После сохранения изменения будут
            отправлены с пометкой [UPD].
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Название</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Описание</FormLabel>
                  <FormControl>
                    <Textarea {...field} rows={6} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Статус</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите статус" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="new">Новая</SelectItem>
                      <SelectItem value="ready">Готова</SelectItem>
                      <SelectItem value="declined">Отклонена</SelectItem>
                      <SelectItem value="sent">Отправлена</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="contact_info"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Контактная информация</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      value={field.value || ""}
                      rows={3}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="deadline_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Дедлайн</FormLabel>
                  <FormControl>
                    <DateTimePicker
                      value={field.value || null}
                      onChange={field.onChange}
                      placeholder="Выберите дату и время дедлайна"
                    />
                  </FormControl>
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
              <Button type="submit" disabled={updatePublication.isPending}>
                Сохранить
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

