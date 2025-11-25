import { useState } from "react"
import { useParsers, useEnableParser, useDisableParser } from "@/hooks/use-parsers"
import { CreateParserDialog } from "@/components/parsers/CreateParserDialog"
import { EditParserDialog } from "@/components/parsers/EditParserDialog"
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
import { FiPlus, FiEdit, FiPower, FiX } from "react-icons/fi"
import { formatParserType } from "@/lib/format"
import { formatDate } from "@/lib/date"
import type { ParserRead } from "@/types/api"

export function ParsersPage() {
  const [creating, setCreating] = useState(false)
  const [editingParser, setEditingParser] = useState<ParserRead | null>(null)

  const { data: parsers, isLoading } = useParsers()
  const enableParser = useEnableParser()
  const disableParser = useDisableParser()

  const handleToggle = async (parser: ParserRead) => {
    if (parser.is_active) {
      await disableParser.mutateAsync(parser.id)
    } else {
      await enableParser.mutateAsync(parser.id)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Парсеры</h1>
        <Button onClick={() => setCreating(true)}>
          <FiPlus className="h-4 w-4 mr-2" />
          Создать парсер
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
                <TableHead>Название источника</TableHead>
                <TableHead>Тип</TableHead>
                <TableHead>Путь к файлу</TableHead>
                <TableHead>Интервал (мин)</TableHead>
                <TableHead>Время начала</TableHead>
                <TableHead>Последний парсинг</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead>Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {parsers && parsers.length > 0 ? (
                parsers.map((parser) => (
                  <TableRow key={parser.id}>
                    <TableCell className="font-medium">
                      {parser.source_name}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {formatParserType(parser.type)}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {parser.executable_file_path}
                    </TableCell>
                    <TableCell>{parser.parsing_interval}</TableCell>
                    <TableCell>
                      {formatDate(parser.parsing_start_time)}
                    </TableCell>
                    <TableCell>
                      {parser.last_parsed_at
                        ? formatDate(parser.last_parsed_at)
                        : "Никогда"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={parser.is_active ? "default" : "secondary"}
                      >
                        {parser.is_active ? "Активен" : "Неактивен"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingParser(parser)}
                        >
                          <FiEdit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggle(parser)}
                        >
                          {parser.is_active ? (
                            <FiX className="h-4 w-4" />
                          ) : (
                            <FiPower className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">
                    Парсеры не найдены
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {creating && (
        <CreateParserDialog open={creating} onOpenChange={setCreating} />
      )}

      {editingParser && (
        <EditParserDialog
          parser={editingParser}
          open={!!editingParser}
          onOpenChange={(open) => !open && setEditingParser(null)}
        />
      )}
    </div>
  )
}
