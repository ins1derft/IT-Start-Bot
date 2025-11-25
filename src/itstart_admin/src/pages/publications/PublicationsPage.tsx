import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { usePublications } from "@/hooks/use-publications"
import { useApproveAndSend } from "@/hooks/use-publications"
import { EditPublicationDialog } from "@/components/publications/EditPublicationDialog"
import { DeclinePublicationDialog } from "@/components/publications/DeclinePublicationDialog"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { DatePicker } from "@/components/ui/date-picker"
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
import { format } from "date-fns"
import { ru } from "date-fns/locale"
import { FiEye, FiEdit, FiX, FiCheck } from "react-icons/fi"
import type { PublicationRead, PublicationType } from "@/types/api"
import { PUBLICATION_TYPES, PUBLICATION_STATUSES } from "@/lib/constants"

const statusLabels: Record<string, string> = {
  new: "Новая",
  ready: "Готова",
  declined: "Отклонена",
  sent: "Отправлена",
}

const typeLabels: Record<PublicationType, string> = {
  job: "Вакансия",
  internship: "Стажировка",
  conference: "Конференция",
}

export function PublicationsPage() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<{
    pub_type?: PublicationType | null
    status?: string | null
    date_from?: Date | null
    date_to?: Date | null
  }>({})
  const [editingPublication, setEditingPublication] =
    useState<PublicationRead | null>(null)
  const [decliningPublication, setDecliningPublication] =
    useState<PublicationRead | null>(null)
  const [approvingPublication, setApprovingPublication] =
    useState<PublicationRead | null>(null)

  const { data: publications, isLoading } = usePublications(filters)
  const approveAndSend = useApproveAndSend()

  const handleApproveAndSend = async () => {
    if (approvingPublication) {
      await approveAndSend.mutateAsync(approvingPublication.id)
      setApprovingPublication(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Публикации</h1>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <Select
          value={filters.pub_type || "all"}
          onValueChange={(value) =>
            setFilters({
              ...filters,
              pub_type: value === "all" ? null : (value as PublicationType),
            })
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Тип" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все типы</SelectItem>
            {PUBLICATION_TYPES.map((type) => (
              <SelectItem key={type} value={type}>
                {typeLabels[type]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.status || "all"}
          onValueChange={(value) =>
            setFilters({
              ...filters,
              status: value === "all" ? null : value,
            })
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Статус" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все статусы</SelectItem>
            {PUBLICATION_STATUSES.map((status) => (
              <SelectItem key={status} value={status}>
                {statusLabels[status]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <DatePicker
          value={filters.date_from || null}
          onChange={(date) =>
            setFilters({ ...filters, date_from: date || null })
          }
          placeholder="Дата начала"
          className="w-[180px]"
        />

        <DatePicker
          value={filters.date_to || null}
          onChange={(date) =>
            setFilters({ ...filters, date_to: date || null })
          }
          placeholder="Дата окончания"
          className="w-[180px]"
        />
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Название</TableHead>
                <TableHead>Тип</TableHead>
                <TableHead>Компания</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead>Дата создания</TableHead>
                <TableHead>Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {publications && publications.length > 0 ? (
                publications.map((pub) => (
                  <TableRow key={pub.id}>
                    <TableCell className="font-medium">{pub.title}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{typeLabels[pub.type]}</Badge>
                    </TableCell>
                    <TableCell>{pub.company}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          pub.status === "sent"
                            ? "default"
                            : pub.status === "declined"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {statusLabels[pub.status] || pub.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {format(new Date(pub.created_at), "dd.MM.yyyy HH:mm", {
                        locale: ru,
                      })}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/publications/${pub.id}`)}
                        >
                          <FiEye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingPublication(pub)}
                        >
                          <FiEdit className="h-4 w-4" />
                        </Button>
                        {pub.status !== "declined" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDecliningPublication(pub)}
                          >
                            <FiX className="h-4 w-4" />
                          </Button>
                        )}
                        {pub.status === "ready" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setApprovingPublication(pub)}
                          >
                            <FiCheck className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} className="text-center">
                    Публикации не найдены
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Dialogs */}
      {editingPublication && (
        <EditPublicationDialog
          publication={editingPublication}
          open={!!editingPublication}
          onOpenChange={(open) => !open && setEditingPublication(null)}
        />
      )}

      {decliningPublication && (
        <DeclinePublicationDialog
          publication={decliningPublication}
          open={!!decliningPublication}
          onOpenChange={(open) => !open && setDecliningPublication(null)}
        />
      )}

      <AlertDialog
        open={!!approvingPublication}
        onOpenChange={(open) => !open && setApprovingPublication(null)}
      >
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
