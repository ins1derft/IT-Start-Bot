# IT-Start Bot / Core API

Монорепо для Telegram-бота (aiogram 3) и backend админки (FastAPI) с общим доменным слоем.

## Структура

- `src/itstart_domain` — общие доменные модели и enum’ы.
- `src/itstart_core_api` — FastAPI-приложение админки и внутренних API.
- `src/itstart_tg_bot` — Telegram-бот.
- `docs/` — проектная документация (ТЗ, устав, схема БД).

## Быстрый старт

1. Создать `.env` на основе `.env.example` (DSN по умолчанию: `postgresql+asyncpg://itstart:itstart@localhost:5432/itstart`).
2. Установить зависимости: `poetry install` (Python 3.10+) — создаст изолированный venv.
3. Применить миграции: `alembic upgrade head` (используется DSN из `alembic.ini` или переменная `POSTGRES_DSN`).
4. Запустить API: `poetry run itstart-core-api`.
5. Запустить бота: `poetry run itstart-tg-bot` (перед стартом проверяет подключение к БД).

## Docker
- Сборка и запуск: `docker-compose up --build`
- Переменные окружения читаются из `.env` (DSNы по умолчанию смотрят на контейнеры `db`, `redis`).
- Миграции применяются автоматически при старте `core-api` сервиса.

## Качество

- black + isort + ruff + mypy (pre-commit настроен).
- Полные type hints обязательны.
