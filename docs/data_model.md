# Data Model (aligned with DB schema)

## Enums (факт)
- `publication_type`: job | internship | conference
- `publication_status`: new | declined | ready | sent
- `tag_category`: format | occupation | platform | language | location | technology | duration
- `admin_role`: admin | moderator
- `parser_type`: api_client | website_parser | tg_channel_parser

## Tables
- `publication`
  - id (uuid PK), title, description, type (publication_type), company, url (unique)
  - source_id (uuid, nullable)
  - created_at, vacancy_created_at
  - updated_at, editor_id (uuid, nullable)
  - is_edited bool, is_declined bool, status (publication_status), decline_reason text, deadline_notified bool
  - deadline_at (nullable)
  - contact_info (plain, nullable), contact_info_encrypted bytea (PGP data)
- `tag`: id (uuid PK), name, category (tag_category), unique (name, category)
- `publication_tags`: PK (publication_id, tag_id), FK -> publication, tag (cascade)
- `tg_user`
  - id (uuid PK), tg_id bigint unique
  - register_at, refused_at nullable, is_active bool
- `tg_user_subscriptions`
  - id (uuid PK), user_id FK -> tg_user(id)
  - publication_type (enum), deadline_reminder bool
  - unique (user_id, publication_type)
- `tg_user_subscription_tags`: PK (subscription_id, tag_id), FK -> subscription, tag
- `user_preferences`: PK (user_id, tag_id), FK -> tg_user(id), tag(id) — глобальные предпочтения вне привязки к типу
- `parser`: id (uuid PK), source_name, executable_file_path, type (parser_type), parsing_interval int, parsing_start_time timestamp, last_parsed_at timestamp, is_active bool
- `parsing_result`: id (uuid PK), date, parser_id FK -> parser, success bool, received_amount int
- `admin_user`: id (uuid PK), username unique, password_hash, role (admin_role), is_active bool, otp_secret nullable, created_at default now()
- `publication_schedule`: id (uuid PK), publication_type (enum), interval_minutes int, start_time timestamp null, is_active bool, updated_at timestamp

## Relationships
- publication : tag — many-to-many via publication_tags
- tg_user : tg_user_subscriptions — 1:N (per publication_type)
- tg_user_subscriptions : tag — many-to-many via tg_user_subscription_tags
- tg_user : tag — many-to-many via user_preferences (глобальные теги)
- parser : parsing_result — 1:N
- admin_user referenced from publication.editor_id (logical, FK может быть добавлен по требованию)

## Indices
- publication (type, created_at desc)
- publication_tags (tag_id)
- parsing_result (parser_id, date)
- tg_user (refused_at)
- tg_user_subscriptions (user_id, publication_type)
- publication_schedule (publication_type)
