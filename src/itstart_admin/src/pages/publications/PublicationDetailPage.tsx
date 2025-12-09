import { useParams, useNavigate } from "react-router-dom"
import { usePublication, useApproveAndSend, useDeletePublication } from "@/hooks/use-publications"
import { EditPublicationDialog } from "@/components/publications/EditPublicationDialog"
import { DeclinePublicationDialog } from "@/components/publications/DeclinePublicationDialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
import { formatDate } from "@/lib/date"
import { formatPublicationType, formatStatus } from "@/lib/format"
import { FiEdit, FiX, FiCheck, FiArrowLeft, FiExternalLink, FiTrash2 } from "react-icons/fi"
import { useState } from "react"

export function PublicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: publication, isLoading } = usePublication(id || "")
  const approveAndSend = useApproveAndSend()
  const deletePublication = useDeletePublication()
  const [editing, setEditing] = useState(false)
  const [declining, setDeclining] = useState(false)
  const [approving, setApproving] = useState(false)

  const handleApproveAndSend = async () => {
    if (id) {
      await approveAndSend.mutateAsync(id)
      setApproving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!publication) {
    return (
      <div>
        <p>Публикация не найдена</p>
        <Button onClick={() => navigate("/publications")}>Назад</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/publications")}
          >
            <FiArrowLeft className="h-4 w-4 mr-2" />
            Назад
          </Button>
          <h1 className="text-3xl font-bold">{publication.title}</h1>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setEditing(true)}
          >
            <FiEdit className="h-4 w-4 mr-2" />
            Редактировать
          </Button>
          <Button
            variant="destructive"
            onClick={() => {
              if (id) {
                deletePublication.mutate(id, {
                  onSuccess: () => navigate("/publications"),
                })
              }
            }}
          >
            <FiTrash2 className="h-4 w-4 mr-2" />
            Удалить
          </Button>
          {publication.status !== "declined" && (
            <Button
              variant="outline"
              onClick={() => setDeclining(true)}
            >
              <FiX className="h-4 w-4 mr-2" />
              Отклонить
            </Button>
          )}
          {publication.status === "ready" && (
            <Button onClick={() => setApproving(true)}>
              <FiCheck className="h-4 w-4 mr-2" />
              Одобрить и отправить
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Основная информация</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Тип</p>
              <Badge variant="outline">
                {formatPublicationType(publication.type)}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Компания</p>
              <p className="font-medium">{publication.company}</p>
            </div>
            {publication.editor_id && (
              <div>
                <p className="text-sm text-muted-foreground">Редактор</p>
                <p className="font-mono text-sm break-all">{publication.editor_id}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-muted-foreground">Статус</p>
              <Badge
                variant={
                  publication.status === "sent"
                    ? "default"
                    : publication.status === "declined"
                    ? "destructive"
                    : "secondary"
                }
              >
                {formatStatus(publication.status)}
              </Badge>
              {publication.is_edited && (
                <Badge variant="outline" className="ml-2">
                  UPD
                </Badge>
              )}
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Ссылка</p>
              <a
                href={publication.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline flex items-center gap-1"
              >
                {publication.url}
                <FiExternalLink className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Даты</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Дата создания</p>
              <p>{formatDate(publication.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">
                Дата публикации вакансии
              </p>
              <p>{formatDate(publication.vacancy_created_at)}</p>
            </div>
            {publication.updated_at && (
              <div>
                <p className="text-sm text-muted-foreground">
                  Дата обновления
                </p>
                <p>{formatDate(publication.updated_at)}</p>
              </div>
            )}
            {publication.deadline_at && (
              <div>
                <p className="text-sm text-muted-foreground">Дедлайн</p>
                <p>{formatDate(publication.deadline_at)}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Описание</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap">{publication.description}</p>
        </CardContent>
      </Card>

      {publication.contact_info && (
        <Card>
          <CardHeader>
            <CardTitle>Контактная информация</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap">{publication.contact_info}</p>
          </CardContent>
        </Card>
      )}

      {publication.tags && publication.tags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Теги</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {publication.tags.map((tag) => (
                <Badge key={tag.id} variant="secondary">
                  {tag.name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {publication.is_declined && publication.decline_reason && (
        <Card>
          <CardHeader>
            <CardTitle>Причина отклонения</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{publication.decline_reason}</p>
          </CardContent>
        </Card>
      )}

      {editing && (
        <EditPublicationDialog
          publication={publication}
          open={editing}
          onOpenChange={setEditing}
        />
      )}

      {declining && (
        <DeclinePublicationDialog
          publication={publication}
          open={declining}
          onOpenChange={setDeclining}
        />
      )}

      <AlertDialog open={approving} onOpenChange={setApproving}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Подтверждение отправки</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите одобрить и отправить эту публикацию?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleApproveAndSend}>
              Одобрить и отправить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
