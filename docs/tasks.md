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
- Auth/2FA: login + refresh + change password + rate limit + TOTP setup/confirm/disable + VPN/White list IP ГОТОВО; осталось финализировать политику запрета отключения 2FA для admin (логика уже запрещает).
- Admin users: list/create/patch(role,is_active,password)/disable + аудит ГОТОВО; соблюдать права (admin — всё, moderator — только публикации) при новых роутингах.
- Publications: list/get/patch(title/description,is_edited) ГОТОВО; осталось фильтры по дате/типу/тегам, статусы модерации (новая/отклонена/готова/отправлена), decline с reason, approve-and-send, editor_id, [UPD]-рассылка при изменениях.
- Tags: CRUD ГОТОВО; требуется предзаполнение базовых значений по категориям из ТЗ.
- Parsers & schedule: list/add/update/enable/disable; управление расписанием рассылки публикаций — НЕ ГОТОВО.
- Stats (по ТЗ): sub/unsub за период + дельта; активные пользователи; топ-5 тегов; % ошибок парсера; новые публикации по дням — НЕ ГОТОВО.
- Export: публикации+теги за период CSV/XLSX — НЕ ГОТОВО.
- Logging/observability: Sentry интеграция обязательна; Prometheus метрики; защита от SQLi через валидацию/ORM — частично (ORM есть, Sentry/метрики нет).

## Telegram Bot
- FSM для /subscribe (поштучно по категориям) и /unsubscribe частичной/полной.
- Парсинг аргументов для /subscribe, /unsubscribe, /jobs|/internships|/conferences (ru/lat, #tag).
- /preferences: группировка по категориям, inline edit/delete.
- Поиск: последние 10 not declined по типу; фильтр по тегам пересечением.
- Уведомления: новые публикации по расписанию; дедлайны (deadline_at) с учётом `deadline_reminder`.
- Block handling: `my_chat_member` → refused_at, is_active=false, чистка предпочтений.
- Формат сообщений: единый шаблон + [UPD] при изменении.
- Рассылка в канал по расписанию; Redis кеш горячих выборок; [UPD] при изменении публикаций (согласно ТЗ).

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
