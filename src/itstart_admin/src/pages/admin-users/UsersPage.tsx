import { useState } from "react"
import { useUsers, useDisableUser, useUpdateUser } from "@/hooks/use-admin-users"
import { CreateUserDialog } from "@/components/admin-users/CreateUserDialog"
import { EditUserDialog } from "@/components/admin-users/EditUserDialog"
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
import { formatRole } from "@/lib/format"
import { formatDate } from "@/lib/date"
import { getUser } from "@/lib/auth"
import { FiPlus, FiEdit, FiX, FiCheck } from "react-icons/fi"
import type { AdminUserRead } from "@/types/api"

export function UsersPage() {
  const [creating, setCreating] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUserRead | null>(null)
  const [blockingUser, setBlockingUser] = useState<AdminUserRead | null>(null)

  const me = getUser()

  const { data: users, isLoading } = useUsers()
  const disableUser = useDisableUser()
  const updateUser = useUpdateUser()

  const handleBlockConfirm = async () => {
    if (!blockingUser) return
    await disableUser.mutateAsync(blockingUser.id)
    setBlockingUser(null)
  }

  const handleUnblock = async (user: AdminUserRead) => {
    await updateUser.mutateAsync({ userId: user.id, is_active: true })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Пользователи</h1>
        <Button onClick={() => setCreating(true)}>
          <FiPlus className="h-4 w-4 mr-2" />
          Создать пользователя
        </Button>
      </div>

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
                <TableHead>Имя пользователя</TableHead>
                <TableHead>Роль</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead>Создан</TableHead>
                <TableHead>Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users && users.length > 0 ? (
                users.map((u) => {
                  const isSelf = me?.username === u.username
                  return (
                    <TableRow key={u.id}>
                      <TableCell className="font-medium">{u.username}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{formatRole(u.role)}</Badge>
                      </TableCell>
                      <TableCell>
                        {u.is_active ? (
                          <Badge>Активен</Badge>
                        ) : (
                          <Badge variant="destructive">Заблокирован</Badge>
                        )}
                      </TableCell>
                      <TableCell>{formatDate(u.created_at)}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingUser(u)}
                          >
                            <FiEdit className="h-4 w-4" />
                          </Button>

                          {u.is_active ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={isSelf || disableUser.isPending}
                              title={isSelf ? "Нельзя заблокировать самого себя" : "Заблокировать"}
                              onClick={() => setBlockingUser(u)}
                            >
                              <FiX className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={updateUser.isPending}
                              title="Разблокировать"
                              onClick={() => handleUnblock(u)}
                            >
                              <FiCheck className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="text-center">
                    Пользователи не найдены
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {creating && (
        <CreateUserDialog open={creating} onOpenChange={setCreating} />
      )}

      {editingUser && (
        <EditUserDialog
          user={editingUser}
          open={!!editingUser}
          onOpenChange={(open) => !open && setEditingUser(null)}
        />
      )}

      <AlertDialog
        open={!!blockingUser}
        onOpenChange={(open) => !open && setBlockingUser(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Подтверждение блокировки</AlertDialogTitle>
            <AlertDialogDescription>
              Заблокировать пользователя "{blockingUser?.username}"?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleBlockConfirm}>
              Заблокировать
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
