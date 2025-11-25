import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { updateScheduleSchema } from "@/lib/schemas"
import type { z } from "zod"
import { usePublicationSchedule, useUpdateSchedule } from "@/hooks/use-schedule"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate } from "@/lib/date"
import type { PublicationType } from "@/types/api"

type UpdateScheduleFormValues = z.infer<typeof updateScheduleSchema>

const typeLabels: Record<PublicationType, string> = {
  job: "Вакансии",
  internship: "Стажировки",
  conference: "Конференции",
}

export function SchedulePage() {
  const { data: schedule, isLoading } = usePublicationSchedule()
  const updateSchedule = useUpdateSchedule()

  const form = useForm<UpdateScheduleFormValues>({
    resolver: zodResolver(updateScheduleSchema),
    defaultValues: {
      job_interval_minutes: null,
      internship_interval_minutes: null,
      conference_interval_minutes: null,
    },
  })

  // Update form when schedule data loads
  useEffect(() => {
    if (schedule && !form.formState.isDirty) {
      const jobSchedule = schedule.find((s) => s.publication_type === "job")
      const internshipSchedule = schedule.find(
        (s) => s.publication_type === "internship"
      )
      const conferenceSchedule = schedule.find(
        (s) => s.publication_type === "conference"
      )

      form.reset({
        job_interval_minutes: jobSchedule?.interval_minutes || null,
        internship_interval_minutes: internshipSchedule?.interval_minutes || null,
        conference_interval_minutes: conferenceSchedule?.interval_minutes || null,
      })
    }
  }, [schedule, form])

  const onSubmit = async (data: UpdateScheduleFormValues) => {
    await updateSchedule.mutateAsync(data)
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Расписание рассылки</h1>

      <div className="grid gap-6 md:grid-cols-3">
        {schedule?.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <CardTitle>{typeLabels[item.publication_type]}</CardTitle>
              <CardDescription>
                Настройки расписания для {typeLabels[item.publication_type].toLowerCase()}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Интервал (минуты)</p>
                <p className="text-lg font-semibold">
                  {item.interval_minutes}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Время начала</p>
                <p className="text-lg font-semibold">
                  {item.start_time
                    ? formatDate(item.start_time)
                    : "Не установлено"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Статус</p>
                <p className="text-lg font-semibold">
                  {item.is_active ? "Активно" : "Неактивно"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">
                  Последнее обновление
                </p>
                <p className="text-sm">{formatDate(item.updated_at)}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Изменить интервалы</CardTitle>
          <CardDescription>
            Измените интервалы рассылки для каждого типа публикаций (в минутах)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4"
            >
              <FormField
                control={form.control}
                name="job_interval_minutes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Интервал для вакансий (минуты)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        value={field.value || ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value
                              ? Number(e.target.value)
                              : null
                          )
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="internship_interval_minutes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Интервал для стажировок (минуты)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        value={field.value || ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value
                              ? Number(e.target.value)
                              : null
                          )
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="conference_interval_minutes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Интервал для конференций (минуты)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        value={field.value || ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value
                              ? Number(e.target.value)
                              : null
                          )
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" disabled={updateSchedule.isPending}>
                Сохранить изменения
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
