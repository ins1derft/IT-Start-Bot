// Types from OpenAPI schema

export type AdminRole = "admin" | "moderator"

export type PublicationType = "job" | "internship" | "conference" | "contest"

export type TagCategory =
  | "format"
  | "occupation"
  | "platform"
  | "language"
  | "location"
  | "technology"
  | "duration"

export type ParserType = "api_client" | "website_parser" | "tg_channel_parser"

export interface AdminUserRead {
  id: string
  username: string
  role: AdminRole
  is_active: boolean
  created_at: string
}

export interface TagRead {
  id: string
  name: string
  category: TagCategory
}

export interface PublicationRead {
  id: string
  title: string
  description: string
  type: PublicationType
  company: string
  url: string
  created_at: string
  vacancy_created_at: string
  updated_at: string | null
  is_edited: boolean
  is_declined: boolean
  deadline_at: string | null
  contact_info: string | null
  tags: TagRead[]
  status: string
  decline_reason: string | null
  editor_id: string | null
}

export interface ParserRead {
  id: string
  source_name: string
  executable_file_path: string
  type: ParserType
  parsing_interval: number
  parsing_start_time: string
  last_parsed_at: string | null
  is_active: boolean
}

export interface PublicationScheduleRead {
  id: string
  publication_type: PublicationType
  interval_minutes: number
  start_time: string | null
  is_active: boolean
  updated_at: string
}

export interface PublicationScheduleUpdate {
  job_interval_minutes?: number | null
  internship_interval_minutes?: number | null
  conference_interval_minutes?: number | null
  contest_interval_minutes?: number | null
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  username: string
  password: string
  otp_code?: string | null
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface TOTPSetupResponse {
  secret: string
  provisioning_uri: string
}

export interface OTPCode {
  code: string
}

export interface HTTPValidationError {
  detail?: Array<{
    loc: (string | number)[]
    msg: string
    type: string
  }>
}
