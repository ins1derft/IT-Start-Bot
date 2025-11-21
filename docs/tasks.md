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
- Publications: list/get/patch(title/description,is_edited,status,contact_info,deadline_at, PGP encrypt) + decline(reason) + approve-and-send (статус sent) + фильтры по статусу/дате/типу/тегам ГОТОВО; осталось: статусы модерации в UI, editor_id отображение.
- Tags: CRUD + автосидинг базовых значений по категориям из ТЗ — ГОТОВО.
- Parsers: list/add/update/enable/disable + аудит ГОТОВО; управление расписанием рассылки публикаций — ГОТОВО.
- Stats (по ТЗ): sub/unsub за период + дельта; активные пользователи; топ-5 тегов; % ошибок парсера; новые публикации по дням — ГОТОВО (эндпоинты /admin/stats).
- Export: публикации+теги за период CSV/XLSX ГОТОВО.
- Logging/observability: Sentry интеграция, Prometheus /metrics, ORM — ГОТОВО.

## Telegram Bot
- FSM для /subscribe (поштучно) и /unsubscribe частичной/полной — базовый вариант готов (state на ввод тегов при пустых аргументах).
- Парсинг аргументов для /subscribe, /unsubscribe, /jobs|/internships|/conferences (ru/lat, #tag) — ГОТОВО.
- /preferences: вывод группировкой по категориям — ГОТОВО.
- Поиск: последние 10 not declined по типу; фильтр по тегам — ГОТОВО.
- Инлайн‑меню: кнопки для подписки/отписки/поиска, подсказки, обязательные типы публикаций и проверка occupation+platform/language для jobs/internships — ГОТОВО.
- Уведомления: новые публикации по расписанию; дедлайны (deadline_at) с учётом `deadline_reminder` — ГОТОВО (Celery задачи, schedule таблица).
- Block handling: `my_chat_member` → refused_at, is_active=false, чистка предпочтений — ГОТОВО.
- Формат сообщений: единый шаблон + [UPD] при изменении — ГОТОВО.
- Рассылка в канал по расписанию; Redis кеш горячих выборок; [UPD] при изменении публикаций — ГОТОВО (через Celery + кеш в поиске).

## Common / Infra
- SQLAlchemy репозитории для Publication, Tag, TgUser, Subscriptions, UserPreferences, Parser, ParsingResult, AdminUser.
- DTO/schemas (Pydantic v2) для API/бота.
- Celery: отправка рассылок, дедлайн-ремайндеры, cleanup старых публикаций — ГОТОВО (tasks + tests).
- PGP encrypt/decrypt для contact_info_encrypted — ГОТОВО.
- Pre-commit подключить в CI — ГОТОВО (workflow ci.yml).
- Метрики/логи: Sentry, Prometheus endpoint, структурированные логи — ГОТОВО.
- Контейнеризация: Dockerfile.core, Dockerfile.bot, docker-compose (db+redis+сервисы); CI job для сборки образов — ГОТОВО (ci.yml).

## Deliverables per milestone
- M1: Domain repos + API auth stub + бот /start,/help + healthz + миграции (готово частично: миграции, healthz, каркас).
- M2: Subscribe/unsubscribe + tag filters + admin CRUD публикаций/тегов + базовый auth.
- M3: Полный auth с 2FA + parsers/schedule + stats + export + Celery рассылки + метрики/Sentry + тесты покрытия ≥80% домена.
