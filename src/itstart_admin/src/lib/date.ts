import { format, parseISO } from "date-fns"
import { ru } from "date-fns/locale"

export function formatDate(date: string | null | undefined): string {
  if (!date) return "-"
  try {
    return format(parseISO(date), "dd.MM.yyyy HH:mm", { locale: ru })
  } catch {
    return date
  }
}

export function formatDateOnly(date: string | null | undefined): string {
  if (!date) return "-"
  try {
    return format(parseISO(date), "dd.MM.yyyy", { locale: ru })
  } catch {
    return date
  }
}

export function formatDateTime(date: string | null | undefined): string {
  if (!date) return "-"
  try {
    return format(parseISO(date), "dd.MM.yyyy HH:mm:ss", { locale: ru })
  } catch {
    return date
  }
}

