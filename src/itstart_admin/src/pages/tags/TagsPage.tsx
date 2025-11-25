import { useState } from "react"
import { useTags, useDeleteTag } from "@/hooks/use-tags"
import { CreateTagDialog } from "@/components/tags/CreateTagDialog"
import { EditTagDialog } from "@/components/tags/EditTagDialog"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { FiPlus, FiEdit, FiTrash2 } from "react-icons/fi"
import { formatTagCategory } from "@/lib/format"
import { TAG_CATEGORIES } from "@/lib/constants"
import type { TagRead, TagCategory } from "@/types/api"

export function TagsPage() {
  const [category, setCategory] = useState<TagCategory | null>(null)
  const [creating, setCreating] = useState(false)
  const [editingTag, setEditingTag] = useState<TagRead | null>(null)
  const [deletingTag, setDeletingTag] = useState<TagRead | null>(null)

  const { data: tags, isLoading } = useTags(category)
  const deleteTag = useDeleteTag()

  const handleDeleteConfirm = async () => {
    if (deletingTag) {
      await deleteTag.mutateAsync(deletingTag.id)
      setDeletingTag(null)
    }
  }

  const tagsByCategory = tags?.reduce(
    (acc: Record<TagCategory, TagRead[]>, tag: TagRead) => {
      if (!acc[tag.category]) {
        acc[tag.category] = []
      }
      acc[tag.category].push(tag)
      return acc
    },
    {} as Record<TagCategory, TagRead[]>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Теги</h1>
        <Button onClick={() => setCreating(true)}>
          <FiPlus className="h-4 w-4 mr-2" />
          Создать тег
        </Button>
      </div>

      <div className="flex gap-4">
        <Select
          value={category || "all"}
          onValueChange={(value: string) =>
            setCategory(value === "all" ? null : (value as TagCategory))
          }
        >
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="Фильтр по категории" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все категории</SelectItem>
            {TAG_CATEGORIES.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {formatTagCategory(cat)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : category ? (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Название</TableHead>
                <TableHead>Категория</TableHead>
                <TableHead>Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tags && tags.length > 0 ? (
                tags.map((tag) => (
                  <TableRow key={tag.id}>
                    <TableCell className="font-medium">{tag.name}</TableCell>
                    <TableCell>{formatTagCategory(tag.category)}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingTag(tag)}
                        >
                          <FiEdit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeletingTag(tag)}
                        >
                          <FiTrash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={3} className="text-center">
                    Теги не найдены
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="space-y-6">
          {TAG_CATEGORIES.map((cat) => {
            const categoryTags = tagsByCategory?.[cat] || []
            if (categoryTags.length === 0) return null

            return (
              <div key={cat} className="border rounded-lg">
                <div className="p-4 border-b bg-muted/50">
                  <h3 className="font-semibold">{formatTagCategory(cat)}</h3>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Название</TableHead>
                      <TableHead>Действия</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {categoryTags.map((tag) => (
                      <TableRow key={tag.id}>
                        <TableCell className="font-medium">
                          {tag.name}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingTag(tag)}
                            >
                              <FiEdit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDeletingTag(tag)}
                            >
                              <FiTrash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )
          })}
        </div>
      )}

      {creating && (
        <CreateTagDialog open={creating} onOpenChange={setCreating} />
      )}

      {editingTag && (
        <EditTagDialog
          tag={editingTag}
          open={!!editingTag}
          onOpenChange={(open) => !open && setEditingTag(null)}
        />
      )}

      <AlertDialog open={!!deletingTag} onOpenChange={(open) => !open && setDeletingTag(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Подтверждение удаления</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить тег "{deletingTag?.name}"? Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
