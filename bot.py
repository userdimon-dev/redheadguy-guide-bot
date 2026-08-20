"""
Telegram-бот RedheadGuy — гайды по настройкам и сервисам.
Работает на aiogram 3.

Запуск:
  python bot.py
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, ErrorEvent, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, BOT_VERSION, BOT_NAME, ADMIN_ID
from guides import load_guides
from keyboards import main_menu_keyboard, category_keyboard, guide_keyboard
from users import register_user, count_users
from states import SearchStates
import admin
import logger as logger_setup  # настраивает логирование (консоль + файл)

# ---------- Логирование ----------
logger = logging.getLogger("bot")

# Аналитический логгер (действия пользователей — просмотры и т.п.)
analytics = logger_setup.get_analytics_logger()


def safe_edit(message, text, **kwargs):
    """Безопасное редактирование сообщения, игнорирует «message is not modified»."""
    try:
        return message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        err = f"{e} {getattr(e, 'message', '')}".lower()
        if "not modified" in err:
            return  # контент уже тот же — пропускаем
        raise


# ---------- Инициализация ----------
# default=DefaultBotProperties(parse_mode=HTML) включает рендеринг
# HTML-разметки (<b>, <a> и т.д.) для всех сообщений
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
dp.include_router(admin.router)

WELCOME_TEXT = (
    "👋 <b>Привет! Я — бот с гайдами RedheadGuy.</b>\n\n"
    "Здесь вы найдёте пошаговые инструкции по настройке приложений, "
    "сервисов и подключению к основному боту.\n\n"
    "Выберите раздел в меню ниже 👇"
)


# ---------- Команда /start ----------
@dp.message(CommandStart())
async def cmd_start(message: Message):
    u = message.from_user
    is_new = register_user(u.id)
    analytics.info("START | user_id=%s | username=%s", u.id, u.username or "-")

    # Уведомление админу о новом пользователе
    if is_new:
        total = count_users()
        for admin_id in ADMIN_ID:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🎉 <b>Новый пользователь!</b>\n\n"
                    f"👤 <b>{u.full_name or u.username or u.id}</b>\n"
                    f"🆔 ID: <code>{u.id}</code>\n"
                    f"📛 @{u.username or '-'}\n\n"
                    f"👥 Всего пользователей: <b>{total}</b>",
                )
            except Exception as e:
                logger.warning("Не удалось уведомить админа %s о новом юзере: %s", admin_id, e)

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
    )


# ---------- Команда /version ----------
@dp.message(F.text == "/version" or F.text.startswith("/version"))
async def cmd_version(message: Message):
    await message.answer(
        f"🤖 <b>{BOT_NAME}</b>\n"
        f"Версия: <b>v{BOT_VERSION}</b>\n\n"
        f"🆕 Проверяйте обновления у @redheadguy_bot"
    )


# ---------- Команда /about ----------
@dp.message(F.text == "/about" or F.text.startswith("/about"))
async def cmd_about(message: Message):
    await message.answer(
        f"ℹ️ <b>{BOT_NAME} v{BOT_VERSION}</b>\n\n"
        "Здесь собраны пошаговые гайды по настройке приложений "
        "и сервисов RedheadGuy.\n\n"
        "Выберите нужный раздел в главном меню 👇\n\n"
        "⚙️ <b>Команды:</b>\n"
        "/start — главное меню\n"
        "/about — информация о боте\n"
        "/version — версия бота"
    )


# ---------- Нажатие на пункт меню / возврат в меню ----------
@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: CallbackQuery):
    keyboard = main_menu_keyboard()
    # Если сообщение уже содержит меню — просто изменяем текст/кнопки
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            WELCOME_TEXT,
            reply_markup=keyboard,
        )
    else:
        await safe_edit(
            callback.message,
            WELCOME_TEXT,
            reply_markup=keyboard,
        )
    await callback.answer()


# ---------- Выбор категории ----------
@dp.callback_query(F.data.startswith("cat:"))
async def choose_category(callback: CallbackQuery):
    category_id = callback.data.split(":", 1)[1]
    guides = load_guides()
    category = guides[category_id]

    u = callback.from_user
    analytics.info(
        "CATEGORY | user_id=%s | category=%s | title=%s",
        u.id, category_id, category.get("title", ""),
    )

    await safe_edit(
        callback.message,
        f"📂 <b>{category['title']}</b>\n\nВыберите нужную инструкцию:",
        reply_markup=category_keyboard(category_id),
    )
    await callback.answer()


# ---------- Показ конкретного гайда ----------
@dp.callback_query(F.data.startswith("guide:"))
async def show_guide(callback: CallbackQuery):
    _, category_id, index_str = callback.data.split(":", 2)
    index = int(index_str)
    guides = load_guides()
    guide = guides[category_id]["guide"][index]

    u = callback.from_user
    analytics.info(
        "GUIDE | user_id=%s | category=%s | guide_idx=%s | title=%s",
        u.id, category_id, index, guide.get("title", ""),
    )

    keyboard = guide_keyboard(category_id, index, guide)
    text = f"<b>{guide['title']}</b>\n\n{guide['text']}"

    # Если есть картинка — отправляем с фото
    if guide.get("photo"):
        photo = FSInputFile(guide["photo"])
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await safe_edit(
            callback.message,
            text,
            reply_markup=keyboard,
        )
    await callback.answer()


# ---------- Поиск по гайдам ----------
def _search_guides(query: str, limit: int = 15) -> list:
    """Ищет гайды по запросу (по заголовку и тексту). Возвращает список (cat, idx, guide)."""
    q = query.lower().strip()
    if not q:
        return []
    guides = load_guides()
    results = []
    for cat_id, cat in guides.items():
        for idx, guide in enumerate(cat.get("guide", [])):
            title = (guide.get("title") or "").lower()
            text = (guide.get("text") or "").lower()
            if q in title or q in text:
                results.append((cat_id, idx, guide))
                if len(results) >= limit:
                    return results
    return results


def search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    """Клавиатура с найденными гайдами + кнопка «В меню»."""
    builder = InlineKeyboardBuilder()
    for cat_id, idx, guide in results:
        builder.button(
            text=guide.get("title", "Гайд"),
            callback_data=f"guide:{cat_id}:{idx}",
        )
    builder.button(text="🏠 В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data == "search")
async def search_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.query)
    await safe_edit(
        callback.message,
        "🔍 <b>Поиск по гайдам</b>\n\n"
        "Введите ключевое слово или фразу для поиска "
        "(например «Windows», «установка»):",
    )
    await callback.answer()


@dp.message(SearchStates.query)
async def search_process(message: Message, state: FSMContext):
    await state.clear()
    query = message.text.strip()

    # Пустой запрос или отмена/start — возвращаем в меню
    if not query or query.lower() in ("/cancel", "/start", "menu"):
        await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())
        return

    results = _search_guides(query)

    if not results:
        await message.answer(
            f"🔍 По запросу <b>«{query}»</b> ничего не найдено.\n\n"
            "Попробуйте другое ключевое слово.",
            reply_markup=main_menu_keyboard(),
        )
        return

    text = f"🔍 Результаты по запросу <b>«{query}»</b> — <b>{len(results)}</b>:\n\n"
    builder = search_results_keyboard(results)
    await message.answer(text, reply_markup=builder)


# ---------- Запуск ----------
@dp.errors()
async def error_handler(event: ErrorEvent):
    """Глобальный перехватчик ошибок. Подавляет «message is not modified»."""
    exc = event.exception
    # Подавляем ошибку повторного редактирования (не критично)
    if isinstance(exc, TelegramBadRequest):
        err = f"{exc} {getattr(exc, 'message', '')}".lower()
        if "not modified" in err:
            logger.debug("Подавлена ошибка 'message is not modified'")
            return True  # значит ошибка обработана, не логируем как ERROR
    # Остальные ошибки логируем как обычно
    logger.error("Ошибка при обработке апдейта: %s", exc)
    return False


async def main():
    try:
        logger.info("%s v%s запущен. Ожидание сообщений...", BOT_NAME, BOT_VERSION)
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")
    except Exception as e:
        logger.exception("Критическая ошибка при работе бота: %s", e)


if __name__ == "__main__":
    asyncio.run(main())

