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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { DateTimePicker } from "@/components/ui/date-picker"
import { PUBLICATION_TYPES } from "@/lib/constants"
import type { PublicationType } from "@/types/api"
import { useCreatePublication } from "@/hooks/use-publications"

const createPublicationSchema = z.object({
  title: z.string().min(1, "Название обязательно"),
  description: z.string().min(1, "Описание обязательно"),
  type: z.enum(["job", "internship", "conference", "contest"] as const),
  company: z.string().min(1, "Компания обязательна"),
  url: z.string().url("Невалидный URL"),
  vacancy_created_at: z.date({ required_error: "Укажите дату публикации" }),
  deadline_at: z.date().optional().nullable(),
  contact_info: z.string().optional().nullable(),
})

type CreatePublicationFormValues = z.infer<typeof createPublicationSchema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreatePublicationDialog({ open, onOpenChange }: Props) {
  const createPublication = useCreatePublication()

  const form = useForm<CreatePublicationFormValues>({
    resolver: zodResolver(createPublicationSchema),
    defaultValues: {
      title: "",
      description: "",
      type: "job",
      company: "",
      url: "",
      vacancy_created_at: new Date(),
      deadline_at: null,
      contact_info: "",
    },
  })

  const onSubmit = async (data: CreatePublicationFormValues) => {
    await createPublication.mutateAsync({
      ...data,
      vacancy_created_at: data.vacancy_created_at.toISOString(),
      deadline_at: data.deadline_at ? data.deadline_at.toISOString() : null,
    })
    if (!createPublication.isPending) {
      form.reset()
      onOpenChange(false)
    }
  }

  const typeLabels: Record<PublicationType, string> = {
    job: "Вакансия",
    internship: "Стажировка",
    conference: "Конференция",
    contest: "Хакатон/конкурс",
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Новая публикация</DialogTitle>
          <DialogDescription>
            Заполните обязательные поля. Дубликаты по ссылке или совпадению
            заголовка+компании+даты будут отклонены.
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
                    <Textarea {...field} rows={5} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Тип</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Выберите тип" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {PUBLICATION_TYPES.map((t) => (
                          <SelectItem key={t} value={t}>
                            {typeLabels[t]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="company"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Компания</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>URL источника</FormLabel>
                    <FormControl>
                      <Input {...field} inputMode="url" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="vacancy_created_at"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Дата/время публикации вакансии</FormLabel>
                    <FormControl>
                      <DateTimePicker
                        value={field.value || null}
                        onChange={field.onChange}
                        placeholder="Выберите дату"
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
                    <FormLabel>Дедлайн (опционально)</FormLabel>
                    <FormControl>
                      <DateTimePicker
                        value={field.value || null}
                        onChange={field.onChange}
                        placeholder="Выберите дату"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="contact_info"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Контакты (опционально)</FormLabel>
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
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Отмена
              </Button>
              <Button type="submit" disabled={createPublication.isPending}>
                Создать
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

