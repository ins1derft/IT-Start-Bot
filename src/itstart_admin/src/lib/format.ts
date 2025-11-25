import type { AdminRole, PublicationType, TagCategory, ParserType } from "@/types/api"

const roles: Record<AdminRole, string> = {
  admin: "Администратор",
  moderator: "Модератор",
}

export function formatRole(role: AdminRole): string {
  return roles[role] || role
}

const types: Record<PublicationType, string> = {
  job: "Вакансия",
  internship: "Стажировка",
  conference: "Конференция",
}

export function formatPublicationType(type: PublicationType): string {
  return types[type] || type
}
const categories: Record<TagCategory, string> = {
  format: "Формат работы",
  occupation: "Специализация",
  platform: "Платформа",
  language: "Язык",
  location: "Локация",
  technology: "Технология",
  duration: "График",
}

export function formatTagCategory(category: TagCategory): string {
  return categories[category] || category
}

const parsers: Record<ParserType, string> = {
  api_client: "API клиент",
  website_parser: "Парсер сайта",
  tg_channel_parser: "Парсер Telegram канала",
}

export function formatParserType(type: ParserType): string {
  return parsers[type] || type
}

const statuses: Record<string, string> = {
  new: "Новая",
  declined: "Отклонена",
  ready: "Готова",
  sent: "Отправлена",
}

export function formatStatus(status: string): string {
  return statuses[status] || status
}

