# ADR-0001: Backend + TG Bot Architecture

## Context
- Нам принадлежит зона: Telegram-бот (aiogram 3) и backend админки (FastAPI) без изменения инфраструктуры.
- Единый источник данных — PostgreSQL 15+, схема согласована с БД-командой (см. docs/data_model.md).
- Redis используется для кеша и FSM бота; Celery для рассылок/напоминаний.
- Требования безопасности: 2FA для админов, Argon2 пароли, PGP для контактной информации, Sentry логирование, Prometheus метрики.

## Decision
- Monorepo с сервисами: `itstart_core_api` (FastAPI), `itstart_tg_bot` (aiogram), общий пакет `itstart_domain` + `itstart_common` (infra).
- async стек: SQLAlchemy 2.x + asyncpg, Alembic для миграций; общая DSN `POSTGRES_DSN`.
- Доменные модели с UUID первичными ключами; у tg_user сохраняем и UUID id, и `tg_id` (unique). Типы публикаций и категорий тегов — ENUM в БД и в коде.
- Рассылки и дедлайны — Celery (broker Redis); бот и API могут триггерить задачи.
- Аутентификация админки: JWT/сессии (реализация TBD) с Argon2 паролями и TOTP; логины и действия логируем в аудит и Sentry.

## Status
Accepted (2025-11-21)

## Consequences
- Общий доменный слой уменьшает расхождения между ботом и API.
- Требует строгой синхронизации миграций и моделей; изменения схемы идут через Alembic и согласование с БД-командой.
- Все сервисы обязаны использовать async stack; любые raw-SQL запрещены вне миграций.
