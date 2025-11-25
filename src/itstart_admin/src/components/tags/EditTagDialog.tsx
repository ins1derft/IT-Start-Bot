import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { updateTagSchema } from "@/lib/schemas"
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
import { useUpdateTag } from "@/hooks/use-tags"
import { TAG_CATEGORIES } from "@/lib/constants"
import type { TagRead, TagCategory } from "@/types/api"

type UpdateTagFormValues = z.infer<typeof updateTagSchema>

interface EditTagDialogProps {
  tag: TagRead
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

export function EditTagDialog({ tag, open, onOpenChange }: EditTagDialogProps) {
  const updateTag = useUpdateTag()

  const form = useForm<UpdateTagFormValues>({
    resolver: zodResolver(updateTagSchema),
    defaultValues: {
      name: tag.name,
      category: tag.category,
    },
  })

  const onSubmit = async (data: UpdateTagFormValues) => {
    await updateTag.mutateAsync({
      tagId: tag.id,
      ...data,
    })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Редактировать тег</DialogTitle>
          <DialogDescription>
            Измените данные тега. Изменения будут применены ко всем
            публикациям, использующим этот тег.
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
                    <Input {...field} />
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
              <Button type="submit" disabled={updateTag.isPending}>
                Сохранить
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

