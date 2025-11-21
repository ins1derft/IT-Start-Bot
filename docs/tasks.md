# Tasks (приоритеты для роли «Разработчик бэкенда админки + ТГ‑бот»)

**Спринт 0 — сделано**
- [x] Каркас монорепо (FastAPI + aiogram 3 + общий домен).
- [x] Базовые миграции 0001/0002, синхронизация с ТЗ по БД.
- [x] DDL/ADR/конституция зафиксированы.
- [x] Docker окружение (db, redis, core-api, tg-bot), токен бота установлен.
- [x] SQLAlchemy модели + репозитории, сессионные зависимости; smoke-проверка ORM vs БД.
- [x] Базовые автотесты (healthz, ORM репозитории) и pytest каркас.
- [x] Pydantic схемы (read) и тесты на них.

## Core API (admin panel)
- Auth/2FA: login + refresh + change password + rate limit готовы; осталось setup/confirm/disable TOTP.
- Admin users: list/create + patch (role/is_active/password) + disable готовы; осталось аудит (admin/moderator).
- Publications CRUD: list/get/patch (title/description, is_edited) готово; осталось фильтры по тегам/статусам, decline+reason, approve-and-send, editor_id.
- Tags CRUD (enum category, unique (name, category)) — базовый list/create/update/delete готов.
- Parsers & schedule: list/add/update/enable/disable; schedule endpoints для рассылок.
- Stats: users (sub/unsub delta), active users, top-5 tags, parser error %, publications per day.
- Export: publications+tags CSV/XLSX by date range.
- Metrics/health: `/healthz` (готово), Prometheus metrics, Sentry контекст.

## Telegram Bot
- FSM для /subscribe (поштучно по категориям) и /unsubscribe частичной/полной.
- Парсинг аргументов для /subscribe, /unsubscribe, /jobs|/internships|/conferences (ru/lat, #tag).
- /preferences: группировка по категориям, inline edit/delete.
- Поиск: последние 10 not declined по типу; фильтр по тегам пересечением.
- Уведомления: новые публикации по расписанию; дедлайны (deadline_at) с учётом `deadline_reminder`.
- Block handling: `my_chat_member` → refused_at, is_active=false, чистка предпочтений.
- Формат сообщений: единый шаблон + [UPD] при изменении.

## Common / Infra
- SQLAlchemy репозитории для Publication, Tag, TgUser, Subscriptions, UserPreferences, Parser, ParsingResult, AdminUser.
- DTO/schemas (Pydantic v2) для API/бота.
- Celery: отправка рассылок, дедлайн-ремайндеры, cleanup старых публикаций.
- PGP encrypt/decrypt для contact_info_encrypted.
- Pre-commit подключить в CI.
- Метрики/логи: Sentry, Prometheus endpoint, структурированные логи.
- Контейнеризация: Dockerfile.core, Dockerfile.bot, docker-compose (db+redis+сервисы); CI job для сборки образов.

## Deliverables per milestone
- M1: Domain repos + API auth stub + бот /start,/help + healthz + миграции (готово частично: миграции, healthz, каркас).
- M2: Subscribe/unsubscribe + tag filters + admin CRUD публикаций/тегов + базовый auth.
- M3: Полный auth с 2FA + parsers/schedule + stats + export + Celery рассылки + метрики/Sentry + тесты покрытия ≥80% домена.
