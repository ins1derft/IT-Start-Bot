import { useState } from "react"
import {
  useUsersStats,
  useTagsTop,
  useParsersErrorPercent,
  usePublicationsPerDay,
} from "@/hooks/use-stats"
import { ExportDialog } from "@/components/export/ExportDialog"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DatePicker } from "@/components/ui/date-picker"
import { Skeleton } from "@/components/ui/skeleton"
import { FiDownload } from "react-icons/fi"
import { formatDateOnly } from "@/lib/date"

export function StatsPage() {
  const [filters, setFilters] = useState<{
    date_from?: Date | null
    date_to?: Date | null
  }>({})
  const [exportOpen, setExportOpen] = useState(false)

  const { data: usersStats, isLoading: usersLoading } = useUsersStats(filters)
  const { data: tagsTop, isLoading: tagsLoading } = useTagsTop(5)
  const { data: parsersError, isLoading: parsersLoading } =
    useParsersErrorPercent(filters)
  const { data: publicationsPerDay, isLoading: publicationsLoading } =
    usePublicationsPerDay(filters)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Статистика</h1>
        <Button onClick={() => setExportOpen(true)}>
          <FiDownload className="h-4 w-4 mr-2" />
          Экспорт публикаций
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
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

      {/* Users Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Статистика пользователей</CardTitle>
        </CardHeader>
        <CardContent>
          {usersLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : usersStats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Подписки</p>
                <p className="text-2xl font-bold">
                  {usersStats.subscribed || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Отписки</p>
                <p className="text-2xl font-bold">
                  {usersStats.unsubscribed || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Разница</p>
                <p className="text-2xl font-bold">
                  {(usersStats.subscribed || 0) - (usersStats.unsubscribed || 0)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Активные</p>
                <p className="text-2xl font-bold">
                  {usersStats.active || 0}
                </p>
              </div>
            </div>
          ) : (
            <p>Нет данных</p>
          )}
        </CardContent>
      </Card>

      {/* Top Tags */}
      <Card>
        <CardHeader>
          <CardTitle>Топ-5 тегов</CardTitle>
        </CardHeader>
        <CardContent>
          {tagsLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : tagsTop && Array.isArray(tagsTop) ? (
            <div className="space-y-2">
              {tagsTop.map((tag: any, index: number) => (
                <div
                  key={tag.id || index}
                  className="flex items-center justify-between p-2 border rounded"
                >
                  <span>{tag.name || tag.tag_name || `Тег ${index + 1}`}</span>
                  <span className="font-semibold">
                    {tag.count || tag.usage_count || 0}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p>Нет данных</p>
          )}
        </CardContent>
      </Card>

      {/* Parsers Error Percent */}
      <Card>
        <CardHeader>
          <CardTitle>Процент ошибок парсеров</CardTitle>
        </CardHeader>
        <CardContent>
          {parsersLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : parsersError ? (
            <div>
              <p className="text-3xl font-bold">
                {typeof parsersError === "number"
                  ? `${parsersError.toFixed(2)}%`
                  : parsersError.error_percent
                  ? `${parsersError.error_percent.toFixed(2)}%`
                  : "0%"}
              </p>
            </div>
          ) : (
            <p>Нет данных</p>
          )}
        </CardContent>
      </Card>

      {/* Publications Per Day */}
      <Card>
        <CardHeader>
          <CardTitle>Публикации по дням</CardTitle>
        </CardHeader>
        <CardContent>
          {publicationsLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : publicationsPerDay && Array.isArray(publicationsPerDay) ? (
            <div className="space-y-2">
              {publicationsPerDay.map((item: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 border rounded"
                >
                  <span>
                    {item.date
                      ? formatDateOnly(item.date)
                      : `День ${index + 1}`}
                  </span>
                  <span className="font-semibold">
                    {item.count || item.publications_count || 0}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p>Нет данных</p>
          )}
        </CardContent>
      </Card>

      {exportOpen && (
        <ExportDialog open={exportOpen} onOpenChange={setExportOpen} />
      )}
    </div>
  )
}
