import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { createTagSchema } from "@/lib/schemas"
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
import { useCreateTag } from "@/hooks/use-tags"
import { TAG_CATEGORIES } from "@/lib/constants"
import type { TagCategory } from "@/types/api"

type CreateTagFormValues = z.infer<typeof createTagSchema>

interface CreateTagDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const categoryLabels: Record<TagCategory, string> = {
  format: "Формат работы",
  occupation: "Специализация",
  platform: "Платформа",
  language: "Язык",
  location: "Местоположение",
  technology: "Технология",
  duration: "График",
}

export function CreateTagDialog({
  open,
  onOpenChange,
}: CreateTagDialogProps) {
  const createTag = useCreateTag()

  const form = useForm<CreateTagFormValues>({
    resolver: zodResolver(createTagSchema),
    defaultValues: {
      name: "",
      category: "format",
    },
  })

  const onSubmit = async (data: CreateTagFormValues) => {
    await createTag.mutateAsync(data)
    onOpenChange(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Создать тег</DialogTitle>
          <DialogDescription>
            Добавьте новый тег в систему. Тег будет доступен для использования
            в публикациях.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Название</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="Например: React" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Категория</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите категорию" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {TAG_CATEGORIES.map((category) => (
                        <SelectItem key={category} value={category}>
                          {categoryLabels[category]}
                        </SelectItem>
                      ))}
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
              <Button type="submit" disabled={createTag.isPending}>
                Создать
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

