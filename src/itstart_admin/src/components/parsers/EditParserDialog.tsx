import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { updateParserSchema } from "@/lib/schemas"
import type { z } from "zod"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { useUpdateParser } from "@/hooks/use-parsers"
import { PARSER_TYPES } from "@/lib/constants"
import type { ParserRead } from "@/types/api"
import { format } from "date-fns"

type UpdateParserFormValues = z.infer<typeof updateParserSchema>

interface EditParserDialogProps {
  parser: ParserRead
  open: boolean
  onOpenChange: (open: boolean) => void
}

const parserTypeLabels: Record<string, string> = {
  api_client: "API клиент",
  website_parser: "Парсер сайта",
  tg_channel_parser: "Парсер Telegram канала",
}

export function EditParserDialog({
  parser,
  open,
  onOpenChange,
}: EditParserDialogProps) {
  const updateParser = useUpdateParser()

  const form = useForm<UpdateParserFormValues>({
    resolver: zodResolver(updateParserSchema),
    defaultValues: {
      source_name: parser.source_name,
      executable_file_path: parser.executable_file_path,
      type: parser.type,
      parsing_interval: parser.parsing_interval,
      parsing_start_time: format(
        new Date(parser.parsing_start_time),
        "yyyy-MM-dd'T'HH:mm"
      ),
      is_active: parser.is_active,
    },
  })

  const onSubmit = async (data: UpdateParserFormValues) => {
    await updateParser.mutateAsync({
      parserId: parser.id,
      ...data,
    })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Редактировать парсер</DialogTitle>
          <DialogDescription>
            Измените параметры парсера. Изменения вступят в силу после
            сохранения.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="source_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Название источника</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value || ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="executable_file_path"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Путь к исполняемому файлу</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value || ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Тип парсера</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value || undefined}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите тип" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {PARSER_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {parserTypeLabels[type]}
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
              name="parsing_interval"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Интервал парсинга (минуты)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      value={field.value || ""}
                      onChange={(e) =>
                        field.onChange(
                          e.target.value ? Number(e.target.value) : null
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
              name="parsing_start_time"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Время начала парсинга</FormLabel>
                  <FormControl>
                    <Input
                      type="datetime-local"
                      {...field}
                      value={field.value || ""}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value ?? false}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel>Активен</FormLabel>
                  </div>
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
              <Button type="submit" disabled={updateParser.isPending}>
                Сохранить
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

