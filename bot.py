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
from aiogram.types import Message, CallbackQuery, FSInputFile, ErrorEvent
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from guides import load_guides
from keyboards import main_menu_keyboard, category_keyboard, guide_keyboard
import admin
import logger as logger_setup  # настраивает логирование (консоль + файл)

# ---------- Логирование ----------
logger = logging.getLogger("bot")


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
    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
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
        logger.info("Бот запущен. Ожидание сообщений...")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")
    except Exception as e:
        logger.exception("Критическая ошибка при работе бота: %s", e)


if __name__ == "__main__":
    asyncio.run(main())

