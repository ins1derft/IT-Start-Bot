from __future__ import annotations

import asyncio
import logging

import sentry_sdk
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

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


def _format_subscribe_success(result: dict) -> str:
    types = ", ".join([t.value for t in result.get("types", [])]) or "не выбраны"
    unknown = ", ".join(result.get("unknown", [])) or "нет"
    return (
        "✅ Подписка сохранена\n"
        f"• Типы: {types}\n"
        f"• Тегов добавлено: {len(result.get('tags', []))}\n"
        f"• Неизвестные теги: {unknown}"
    )


def _format_unsubscribe_success(result: dict) -> str:
    removed_types = ", ".join(result.get("removed_types", [])) or "нет"
    removed_tags = ", ".join(result.get("removed_tags", [])) or "нет"
    unknown = ", ".join(result.get("unknown", [])) or "нет"
    return (
        "✅ Отписка выполнена\n"
        f"• Типы удалены: {removed_types}\n"
        f"• Теги удалены: {removed_tags}\n"
        f"• Неизвестные теги: {unknown}"
    )


MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Подписаться"), KeyboardButton(text="🚫 Отписаться")],
        [KeyboardButton(text="📋 Предпочтения")],
        [
            KeyboardButton(text="💼 Вакансии"),
            KeyboardButton(text="🧑‍🎓 Стажировки"),
            KeyboardButton(text="🎤 Конференции"),
        ],
        [KeyboardButton(text="ℹ️ Справка")],
    ],
    resize_keyboard=True,
)

SUBSCRIBE_TIP = (
    "📌 Обязательные поля: типы публикаций (jobs / internships / conferences).\n"
    "👉 Для jobs/internships добавьте:\n"
    "   • Сфера (occupation): разработчик, тестировщик, аналитик…\n"
    "   • Платформа или язык (platform/language): ios, android, python, csharp…\n"
    "➕ Опционально: формат (remote/office/hybrid), график (part-time/full-time), город."
)


def _build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    router = Router()

    class SubscribeStates(StatesGroup):
        choose_types = State()
        occupation = State()
        platform = State()
        extra = State()

    class UnsubscribeStates(StatesGroup):
        choose_types = State()
        tags = State()

    @router.message(Command("start"))
    async def cmd_start(message: types.Message) -> None:
        await message.answer(
            "👋 Привет! Я помогу найти вакансии, стажировки и конференции.\n\n"
            "📝 Подписка: /subscribe (или кнопка «Подписаться»)\n"
            "🚫 Отписка: /unsubscribe\n"
            "📋 Предпочтения: /preferences\n"
            "🔎 Поиск: /jobs /internships /conferences\n\n"
            "Нажмите нужную кнопку ниже или введите команду.",
            reply_markup=MAIN_MENU,
        )

    @router.message(Command("help"))
    async def cmd_help(message: types.Message) -> None:
        await message.answer(
            "ℹ️ Справка\n"
            "• /subscribe [теги] — подписка (без аргументов запустит мастер)\n"
            "• /unsubscribe [теги] — отписка (без аргументов запустит мастер)\n"
            "• /preferences — показать сохранённые теги\n"
            "• /jobs /internships /conferences [теги] — быстрый поиск\n\n"
            f"{SUBSCRIBE_TIP}",
            reply_markup=MAIN_MENU,
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
            # старый быстрый режим через пробелы
            tokens = split_tokens(args)
            async with Session() as session:
                try:
                    result = await subscribe_tokens(session, message.from_user.id, tokens)
                except ValueError as exc:
                    await message.answer(f"⚠️ {exc}\n\n{SUBSCRIBE_TIP}", reply_markup=MAIN_MENU)
                    return
            await message.answer(
                _format_subscribe_success(result),
                reply_markup=MAIN_MENU,
            )
            return

        # Пошаговый режим FSM
        await state.set_state(SubscribeStates.choose_types)
        await state.update_data(types=set(), occupation=None, platform=None, extra=[])
        await message.answer(
            "🔸 Шаг 1/4. Выберите типы публикаций (jobs, internships, conferences).\n"
            "Отправляйте по одному слову. Когда закончите — напишите «далее». Для отмены — «отмена».",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="jobs"), KeyboardButton(text="internships")],
                    [KeyboardButton(text="conferences"), KeyboardButton(text="далее")],
                    [KeyboardButton(text="отмена")],
                ],
                resize_keyboard=True,
            ),
        )

    @router.message(SubscribeStates.choose_types)
    async def subscribe_choose_types(message: types.Message, state: FSMContext) -> None:
        text = (message.text or "").strip().lower()
        if text == "отмена":
            await state.clear()
            await message.answer("Отменено.", reply_markup=MAIN_MENU)
            return
        data = await state.get_data()
        chosen: set[str] = set(data.get("types", []))
        allowed = {"jobs", "internships", "conferences"}
        if text == "далее":
            if not chosen:
                await message.answer("⚠️ Нужно выбрать хотя бы один тип.")
                return
            await state.set_state(SubscribeStates.occupation)
            await message.answer(
                "🔸 Шаг 2/4. Сфера (occupation): разработчик, тестировщик, аналитик, devops, дизайнер…\n"
                "Введите одно или несколько слов или напишите «пропустить».",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="пропустить")], [KeyboardButton(text="отмена")]],
                    resize_keyboard=True,
                ),
            )
            return
        if text in allowed:
            if text in chosen:
                chosen.remove(text)
            else:
                chosen.add(text)
            await state.update_data(types=chosen)
            await message.answer(
                f"✅ Выбрано: {', '.join(sorted(chosen)) or 'пусто'}. Напишите ещё тип или «далее».",
            )
        else:
            await message.answer("⚠️ Используйте jobs, internships, conferences или «далее».")

    @router.message(SubscribeStates.occupation)
    async def subscribe_occupation(message: types.Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        if text.lower() == "отмена":
            await state.clear()
            await message.answer("Отменено.", reply_markup=MAIN_MENU)
            return
        if text.lower() != "пропустить":
            await state.update_data(occupation=text)
        await state.set_state(SubscribeStates.platform)
        await message.answer(
            "🔸 Шаг 3/4. Платформа или язык (platform/language): ios, android, python, csharp…\n"
            "Введите через пробел или напишите «пропустить».",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="пропустить")], [KeyboardButton(text="отмена")]],
                resize_keyboard=True,
            ),
        )

    @router.message(SubscribeStates.platform)
    async def subscribe_platform(message: types.Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        if text.lower() == "отмена":
            await state.clear()
            await message.answer("Отменено.", reply_markup=MAIN_MENU)
            return
        if text.lower() != "пропустить":
            await state.update_data(platform=text)
        await state.set_state(SubscribeStates.extra)
        await message.answer(
            "🔸 Шаг 4/4. Доп. параметры: формат (remote/office/hybrid), график (part-time/full-time), "
            "город, технология. Введите через пробел или «пропустить».",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="пропустить")], [KeyboardButton(text="отмена")]],
                resize_keyboard=True,
            ),
        )

    @router.message(SubscribeStates.extra)
    async def subscribe_extra(message: types.Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        if text.lower() == "отмена":
            await state.clear()
            await message.answer("Отменено.", reply_markup=MAIN_MENU)
            return
        if text.lower() != "пропустить":
            extra_tokens = split_tokens(text)
        else:
            extra_tokens = []
        data = await state.get_data()
        tokens: list[str] = []
        tokens.extend(list(data.get("types", [])))
        if occ := data.get("occupation"):
            tokens.extend(split_tokens(str(occ)))
        if plat := data.get("platform"):
            tokens.extend(split_tokens(str(plat)))
        tokens.extend(extra_tokens)

        if message.from_user is None:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        async with Session() as session:
            try:
                result = await subscribe_tokens(session, message.from_user.id, tokens)
            except ValueError as exc:
                await message.answer(f"⚠️ {exc}\n\n{SUBSCRIBE_TIP}", reply_markup=MAIN_MENU)
                await state.clear()
                return
        await state.clear()
        await message.answer(
            _format_subscribe_success(result),
            reply_markup=MAIN_MENU,
        )

    @router.message(Command("unsubscribe"))
    async def cmd_unsubscribe(
        message: types.Message, command: CommandObject, state: FSMContext
    ) -> None:
        if message.from_user is None:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        tokens = split_tokens(command.args or "")
        if tokens:
            async with Session() as session:
                result = await unsubscribe_tokens(session, message.from_user.id, tokens)
            await message.answer(
                _format_unsubscribe_success(result),
                reply_markup=MAIN_MENU,
            )
            return

        # Пошаговый режим
        await state.set_state(UnsubscribeStates.choose_types)
        await state.update_data(types=set(), tags=[])
        await message.answer(
            "Шаг 1/2. Что отключаем: jobs / internships / conferences. "
            "Отправляйте по одному, завершите словом «далее» или напишите «пропустить».",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="jobs"), KeyboardButton(text="internships")],
                    [KeyboardButton(text="conferences"), KeyboardButton(text="далее")],
                    [KeyboardButton(text="пропустить"), KeyboardButton(text="отмена")],
                ],
                resize_keyboard=True,
            ),
        )

    @router.message(UnsubscribeStates.choose_types)
    async def unsubscribe_choose_types(message: types.Message, state: FSMContext) -> None:
        text = (message.text or "").strip().lower()
        if text == "отмена":
            await state.clear()
            await message.answer("Отменено.", reply_markup=MAIN_MENU)
            return
        data = await state.get_data()
        chosen: set[str] = set(data.get("types", []))
        allowed = {"jobs", "internships", "conferences"}
        if text in {"далее", "пропустить"}:
            await state.set_state(UnsubscribeStates.tags)
            await message.answer(
                "Шаг 2/2. Введите теги, от которых нужно отписаться (через пробел), "
                "или напишите «пропустить».",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="пропустить")], [KeyboardButton(text="отмена")]],
                    resize_keyboard=True,
                ),
            )
            await state.update_data(types=chosen)
            return
        if text in allowed:
            if text in chosen:
                chosen.remove(text)
            else:
                chosen.add(text)
            await state.update_data(types=chosen)
            await message.answer(
                f"Выбрано: {', '.join(sorted(chosen)) or 'пусто'}. Добавьте ещё или «далее».",
            )
        else:
            await message.answer(
                "Не понял. Используйте jobs, internships, conferences или «далее»."
            )

    @router.message(UnsubscribeStates.tags)
    async def unsubscribe_tags(message: types.Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        if text.lower() == "отмена":
            await state.clear()
            await message.answer("Отменено.", reply_markup=MAIN_MENU)
            return
        tags_tokens = [] if text.lower() == "пропустить" else split_tokens(text)
        data = await state.get_data()
        tokens = list(data.get("types", [])) + tags_tokens
        if message.from_user is None:
            return
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        async with Session() as session:
            result = await unsubscribe_tokens(session, message.from_user.id, tokens)
        await state.clear()
        await message.answer(
            _format_unsubscribe_success(result),
            reply_markup=MAIN_MENU,
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
            await message.answer(
                "🫙 Предпочтения не заданы. Используйте /subscribe.", reply_markup=MAIN_MENU
            )
            return
        lines = []
        for cat, names in prefs.items():
            pretty_cat = {
                "format": "Формат",
                "occupation": "Сфера",
                "platform": "Платформа",
                "language": "Язык",
                "location": "Город",
                "technology": "Технологии",
                "duration": "График",
            }.get(cat, cat)
            lines.append(f"• {pretty_cat}: {', '.join(names)}")
        await message.answer("📋 Ваши предпочтения:\n" + "\n".join(lines), reply_markup=MAIN_MENU)

    async def handle_search(
        message: types.Message, pub_type: PublicationType, tokens: list[str]
    ) -> None:
        settings = get_settings()
        engine = build_engine(settings)
        Session = build_session_maker(engine)
        async with Session() as session:
            pubs = await search_publications(session, pub_type, tokens)
        if not pubs:
            await message.answer(
                "😕 Ничего не нашли. Попробуйте убрать часть тегов или изменить тип публикаций.",
                reply_markup=MAIN_MENU,
            )
            return
        resp = []
        for p in pubs:
            if isinstance(p, dict):
                resp.append(
                    f"🔗 <b>{p['title']}</b>\n"
                    f"🏢 {p.get('company') or '—'}\n"
                    f"🔗 {p.get('url') or '—'}"
                )
            else:
                icon = {
                    PublicationType.job: "💼",
                    PublicationType.internship: "🧑‍🎓",
                    PublicationType.conference: "🎤",
                }.get(p.type, "🔗")
                deadline = (
                    f"\n🗓 Дедлайн: {p.deadline_at:%d.%m.%Y}"
                    if getattr(p, "deadline_at", None)
                    else ""
                )
                city = getattr(p, "city", None)
                location_line = f"📍 {city}\n" if city else ""
                resp.append(
                    f"{icon} <b>{p.title}</b>\n"
                    f"🏢 {getattr(p, 'company', '—')}\n"
                    f"{location_line}"
                    f"🔗 {p.url}{deadline}"
                )
        await message.answer("\n\n".join(resp[:10]), reply_markup=MAIN_MENU)

    @router.message(Command("jobs"))
    async def cmd_jobs(message: types.Message, command: CommandObject) -> None:
        await handle_search(message, PublicationType.job, split_tokens(command.args or ""))

    @router.message(Command("internships"))
    async def cmd_internships(message: types.Message, command: CommandObject) -> None:
        await handle_search(message, PublicationType.internship, split_tokens(command.args or ""))

    @router.message(Command("conferences"))
    async def cmd_conferences(message: types.Message, command: CommandObject) -> None:
        await handle_search(message, PublicationType.conference, split_tokens(command.args or ""))

    @router.callback_query(F.data == "cmd:subscribe")
    async def cb_subscribe(callback: types.CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        if callback.message:
            await state.set_state(SubscribeStates.choose_types)
            await state.update_data(types=set(), occupation=None, platform=None, extra=[])
            await callback.message.answer(
                "🔸 Шаг 1/4. Выберите типы публикаций (jobs, internships, conferences).\n"
                "Отправляйте по одному слову. Когда закончите — напишите «далее». Для отмены — «отмена».",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="jobs"), KeyboardButton(text="internships")],
                        [KeyboardButton(text="conferences"), KeyboardButton(text="далее")],
                        [KeyboardButton(text="отмена")],
                    ],
                    resize_keyboard=True,
                ),
            )

    @router.callback_query(F.data == "cmd:unsubscribe")
    async def cb_unsubscribe(callback: types.CallbackQuery) -> None:
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                "Отписка: отправьте /unsubscribe «теги» или пусто для полной.",
                reply_markup=MAIN_MENU,
            )

    @router.callback_query(F.data == "cmd:preferences")
    async def cb_preferences(callback: types.CallbackQuery) -> None:
        await callback.answer()
        if callback.message:
            await cmd_preferences(callback.message)

    @router.callback_query(F.data.startswith("cmd:search:"))
    async def cb_search(callback: types.CallbackQuery) -> None:
        await callback.answer()
        if not callback.message or not callback.data:
            return
        target = callback.data.split(":", 2)[-1]
        mapping = {
            "job": PublicationType.job,
            "internship": PublicationType.internship,
            "conference": PublicationType.conference,
        }
        pub_type = mapping.get(target)
        if pub_type and isinstance(callback.message, types.Message):
            await handle_search(callback.message, pub_type, [])

    # Русскоязычные кнопки-короткие пути
    @router.message(F.text.lower().in_({"📝 подписаться", "подписаться"}))
    async def btn_subscribe(message: types.Message, state: FSMContext) -> None:
        await cmd_subscribe(
            message, CommandObject(command="subscribe", prefix="/", args=None), state
        )

    @router.message(F.text.lower().in_({"🚫 отписаться", "отписаться"}))
    async def btn_unsubscribe(message: types.Message, state: FSMContext) -> None:
        await cmd_unsubscribe(
            message, CommandObject(command="unsubscribe", prefix="/", args=None), state
        )

    @router.message(F.text.lower().in_({"📋 предпочтения", "предпочтения"}))
    async def btn_preferences(message: types.Message) -> None:
        await cmd_preferences(message)

    @router.message(F.text.lower().in_({"💼 вакансии", "вакансии"}))
    async def btn_jobs(message: types.Message) -> None:
        await handle_search(message, PublicationType.job, [])

    @router.message(F.text.lower().in_({"🧑‍🎓 стажировки", "стажировки"}))
    async def btn_internships(message: types.Message) -> None:
        await handle_search(message, PublicationType.internship, [])

    @router.message(F.text.lower().in_({"🎤 конференции", "конференции"}))
    async def btn_conferences(message: types.Message) -> None:
        await handle_search(message, PublicationType.conference, [])

    @router.message(F.text.lower().in_({"ℹ️ справка", "справка"}))
    async def btn_help(message: types.Message) -> None:
        await cmd_help(message)

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
