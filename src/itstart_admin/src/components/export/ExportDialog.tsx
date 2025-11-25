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
import { DatePicker } from "@/components/ui/date-picker"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useExportPublications } from "@/hooks/use-export"

const exportSchema = z.object({
  date_from: z.date().optional().nullable(),
  date_to: z.date().optional().nullable(),
  fmt: z.enum(["csv", "xlsx"]).default("csv"),
})

type ExportFormValues = z.infer<typeof exportSchema>

interface ExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ExportDialog({ open, onOpenChange }: ExportDialogProps) {
  const exportPublications = useExportPublications()

  const form = useForm<ExportFormValues>({
    resolver: zodResolver(exportSchema),
    defaultValues: {
      date_from: null,
      date_to: null,
      fmt: "csv",
    },
  })

  const onSubmit = async (data: ExportFormValues) => {
    await exportPublications.mutateAsync({
      date_from: data.date_from ? data.date_from.toISOString().split("T")[0] : null,
      date_to: data.date_to ? data.date_to.toISOString().split("T")[0] : null,
      fmt: data.fmt,
    })
    onOpenChange(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Экспорт публикаций</DialogTitle>
          <DialogDescription>
            Выберите период и формат для экспорта публикаций. Если период не
            указан, будут экспортированы все публикации.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="date_from"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Дата начала</FormLabel>
                  <FormControl>
                    <DatePicker
                      value={field.value || null}
                      onChange={field.onChange}
                      placeholder="Выберите дату начала"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="date_to"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Дата окончания</FormLabel>
                  <FormControl>
                    <DatePicker
                      value={field.value || null}
                      onChange={field.onChange}
                      placeholder="Выберите дату окончания"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="fmt"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Формат</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите формат" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
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
                disabled={exportPublications.isPending}
              >
                Экспортировать
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

