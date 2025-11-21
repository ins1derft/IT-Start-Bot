from __future__ import annotations

import asyncio
import logging

import sentry_sdk
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

from .config import Settings, get_settings
from .db import build_engine, build_session_maker

logger = logging.getLogger(__name__)


def _build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message) -> None:
        await message.answer("Привет! Бот готовится к работе. Скоро здесь появится функционал.")

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message) -> None:
        await message.answer("Команды в разработке. Доступны /start и /help.")

    return dp


async def run_bot(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=1.0)

    engine = build_engine(settings)
    session_maker = build_session_maker(engine)

    async with engine.begin() as conn:
        await conn.run_sync(lambda *_: None)
    logger.info("DB connectivity OK")

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = _build_dispatcher()
    dp["session_maker"] = session_maker

    logger.info("Starting Telegram bot")
    await dp.start_polling(bot)


def run() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    run()
