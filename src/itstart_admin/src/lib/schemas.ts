import { z } from "zod"

export const loginSchema = z.object({
  username: z.string().min(1, "Имя пользователя обязательно"),
  password: z.string().min(1, "Пароль обязателен"),
  otp_code: z.string().optional().nullable(),
})

export const changePasswordSchema = z.object({
  old_password: z.string().min(1, "Текущий пароль обязателен"),
  new_password: z.string().min(8, "Пароль должен быть не менее 8 символов"),
})

export const createUserSchema = z.object({
  username: z.string().min(1, "Имя пользователя обязательно"),
  password: z.string().min(8, "Пароль должен быть не менее 8 символов"),
  role: z.enum(["admin", "moderator"] as const),
})

export const updateUserSchema = z.object({
  role: z.enum(["admin", "moderator"] as const).optional(),
  is_active: z.boolean().optional(),
  password: z.string().min(8, "Пароль должен быть не менее 8 символов").optional().nullable(),
})

export const createTagSchema = z.object({
  name: z.string().min(1, "Название обязательно"),
  category: z.enum([
    "format",
    "occupation",
    "platform",
    "language",
    "location",
    "technology",
    "duration",
  ] as const),
})

export const updateTagSchema = z.object({
  name: z.string().min(1, "Название обязательно"),
  category: z.enum([
    "format",
    "occupation",
    "platform",
    "language",
    "location",
    "technology",
    "duration",
  ] as const),
})

export const createParserSchema = z.object({
  source_name: z.string().min(1, "Название источника обязательно"),
  executable_file_path: z.string().min(1, "Путь к файлу обязателен"),
  type: z.enum(["api_client", "website_parser", "tg_channel_parser"] as const),
  parsing_interval: z.number().int().min(1, "Интервал должен быть положительным числом"),
  parsing_start_time: z.string().min(1, "Время начала обязательно"),
  is_active: z.boolean().default(true),
})

export const updateParserSchema = z.object({
  source_name: z.string().min(1, "Название источника обязательно").optional().nullable(),
  executable_file_path: z.string().min(1, "Путь к файлу обязателен").optional().nullable(),
  type: z.enum(["api_client", "website_parser", "tg_channel_parser"] as const).optional().nullable(),
  parsing_interval: z.number().int().min(1).optional().nullable(),
  parsing_start_time: z.string().min(1).optional().nullable(),
  is_active: z.boolean().optional().nullable(),
})

export const updatePublicationSchema = z.object({
  title: z.string().min(1, "Заголовок обязателен").optional().nullable(),
  description: z.string().optional().nullable(),
  status: z.string().optional().nullable(),
  contact_info: z.string().optional().nullable(),
  deadline_at: z.string().optional().nullable(),
})

export const declinePublicationSchema = z.object({
  reason: z.string().min(1, "Причина отклонения обязательна"),
})

export const updateScheduleSchema = z.object({
  job_interval_minutes: z.number().int().min(1).optional().nullable(),
  internship_interval_minutes: z.number().int().min(1).optional().nullable(),
  conference_interval_minutes: z.number().int().min(1).optional().nullable(),
})

export const otpCodeSchema = z.object({
  code: z.string().min(6, "Код должен содержать 6 цифр").max(6),
})

