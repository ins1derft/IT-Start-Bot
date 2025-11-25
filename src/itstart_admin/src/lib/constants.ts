import type {
  AdminRole,
  PublicationType,
  TagCategory,
  ParserType,
} from "@/types/api"

export const ADMIN_ROLES: AdminRole[] = ["admin", "moderator"]

export const PUBLICATION_TYPES: PublicationType[] = [
  "job",
  "internship",
  "conference",
]

export const TAG_CATEGORIES: TagCategory[] = [
  "format",
  "occupation",
  "platform",
  "language",
  "location",
  "technology",
  "duration",
]

export const PARSER_TYPES: ParserType[] = [
  "api_client",
  "website_parser",
  "tg_channel_parser",
]

export const PUBLICATION_STATUSES = ["new", "declined", "ready", "sent"]

