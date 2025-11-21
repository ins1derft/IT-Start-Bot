from __future__ import annotations

import asyncio
import logging

import sentry_sdk
from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from itstart_domain import PublicationType

from .config import Settings, get_settings
from .db import build_engine, build_session_maker
from .service import (
    block_user,
    get_preferences,
    search_publications,
    split_tokens,
    subscribe_tokens,
    unsubscribe_tokens,
)

logger = logging.getLogger(__name__)


def _build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    router = Router()

    class SubscribeStates(StatesGroup):
        awaiting_tags = State()

    @router.message(Command("start"))
    async def cmd_start(message: types.Message) -> None:
        await message.answer(
            "Привет! Я подберу вакансии, стажировки и конференции.\n"
            "Используй /subscribe <теги> или /subscribe без аргументов для пошаговой настройки.\n"
            "Команды: /subscribe, /unsubscribe, /preferences, /jobs, /internships, /conferences"
        )

    @router.message(Command("help"))
    async def cmd_help(message: types.Message) -> None:
        await message.answer(
            "/subscribe [теги] — подписаться\n"
            "/unsubscribe [теги] — отписаться (без аргументов: полная)\n"
            "/preferences — показать текущие теги\n"
            "/jobs /internships /conferences [теги] — поиск\n"
        )

    @router.message(Command("subscribe"))
    async def cmd_subscribe(
        message: types.Message, command: CommandObject, state: FSMContext
    ) -> None:
        if message.from_user is None:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        args = command.args or ""
        if args.strip():
            tokens = split_tokens(args)
            async with Session() as session:
                result = await subscribe_tokens(session, message.from_user.id, tokens)
            await message.answer(
                f"Подписка сохранена. Типы: {result['types']}; теги: {len(result['tags'])}. Неизвестные: {result['unknown']}"
            )
        else:
            await state.set_state(SubscribeStates.awaiting_tags)
            await message.answer("Введите теги/типы для подписки (через пробел).")

    @router.message(SubscribeStates.awaiting_tags)
    async def cmd_subscribe_tags(message: types.Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        tokens = split_tokens(message.text or "")
        async with Session() as session:
            result = await subscribe_tokens(session, message.from_user.id, tokens)
        await state.clear()
        await message.answer(
            f"Подписка сохранена. Типы: {result['types']}; теги: {len(result['tags'])}. Неизвестные: {result['unknown']}"
        )

    @router.message(Command("unsubscribe"))
    async def cmd_unsubscribe(message: types.Message, command: CommandObject) -> None:
        if message.from_user is None:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        tokens = split_tokens(command.args or "")
        async with Session() as session:
            result = await unsubscribe_tokens(session, message.from_user.id, tokens)
        await message.answer(
            f"Отписка выполнена. Типы: {result['removed_types']}; теги: {result['removed_tags']}; неизвестные: {result['unknown']}"
        )

    @router.message(Command("preferences"))
    async def cmd_preferences(message: types.Message) -> None:
        if message.from_user is None:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        async with Session() as session:
            prefs = await get_preferences(session, message.from_user.id)
        if not prefs:
            await message.answer("Предпочтения не заданы.")
            return
        lines = []
        for cat, names in prefs.items():
            lines.append(f"{cat}: {', '.join(names)}")
        await message.answer("\n".join(lines))

    async def handle_search(
        message: types.Message, pub_type: PublicationType, tokens: list[str]
    ) -> None:
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        async with Session() as session:
            pubs = await search_publications(session, pub_type, tokens)
        if not pubs:
            await message.answer("Ничего не найдено.")
            return
        resp = []
        for p in pubs:
            if isinstance(p, dict):
                resp.append(f"{p['title']} — {p['company']} ({p['url']})")
            else:
                resp.append(f"{p.title} — {p.company} ({p.url})")
        await message.answer("\n".join(resp[:10]))

    @router.message(Command("jobs"))
    async def cmd_jobs(message: types.Message, command: CommandObject) -> None:
        await handle_search(message, PublicationType.job, split_tokens(command.args or ""))

    @router.message(Command("internships"))
    async def cmd_internships(message: types.Message, command: CommandObject) -> None:
        await handle_search(message, PublicationType.internship, split_tokens(command.args or ""))

    @router.message(Command("conferences"))
    async def cmd_conferences(message: types.Message, command: CommandObject) -> None:
        await handle_search(message, PublicationType.conference, split_tokens(command.args or ""))

    @router.my_chat_member()
    async def handle_block(update: types.ChatMemberUpdated) -> None:
        # React to user blocking the bot or leaving
        if update.new_chat_member.status not in {
            ChatMemberStatus.KICKED,
            ChatMemberStatus.LEFT,
        }:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        async with Session() as session:
            await block_user(session, update.from_user.id)

    dp.include_router(router)
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
