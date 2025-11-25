import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { createParserSchema } from "@/lib/schemas"
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
import { useCreateParser } from "@/hooks/use-parsers"
import { PARSER_TYPES } from "@/lib/constants"
import { format } from "date-fns"

type CreateParserFormValues = z.infer<typeof createParserSchema>

interface CreateParserDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const parserTypeLabels: Record<string, string> = {
  api_client: "API клиент",
  website_parser: "Парсер сайта",
  tg_channel_parser: "Парсер Telegram канала",
}

export function CreateParserDialog({
  open,
  onOpenChange,
}: CreateParserDialogProps) {
  const createParser = useCreateParser()

  const form = useForm<CreateParserFormValues>({
    resolver: zodResolver(createParserSchema),
    defaultValues: {
      source_name: "",
      executable_file_path: "",
      type: "api_client",
      parsing_interval: 360,
      parsing_start_time: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
      is_active: true,
    },
  })

  const onSubmit = async (data: CreateParserFormValues) => {
    await createParser.mutateAsync(data)
    onOpenChange(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Создать парсер</DialogTitle>
          <DialogDescription>
            Добавьте новый источник парсинга. Парсер будет запускаться согласно
            указанному расписанию.
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
                    <Input {...field} placeholder="Например: HeadHunter API" />
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
                    <Input
                      {...field}
                      placeholder="/path/to/parser/script.py"
                    />
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
                    defaultValue={field.value}
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
                      onChange={(e) => field.onChange(Number(e.target.value))}
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
                    <Input type="datetime-local" {...field} />
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
                      checked={field.value}
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
              <Button type="submit" disabled={createParser.isPending}>
                Создать
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

