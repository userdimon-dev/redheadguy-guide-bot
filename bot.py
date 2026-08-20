
"""
Telegram-бот RedheadGuy — гайды по настройкам и сервисам.
Работает на aiogram 3.

Запуск:
  python bot.py
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from config import BOT_TOKEN
from guides import GUIDES
from keyboards import main_menu_keyboard, category_keyboard, guide_keyboard

# ---------- Логирование ----------
logging.basicConfig(level=logging.INFO)

# ---------- Инициализация ----------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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
        await callback.message.edit_text(
            WELCOME_TEXT,
            reply_markup=keyboard,
        )
    await callback.answer()


# ---------- Выбор категории ----------
@dp.callback_query(F.data.startswith("cat:"))
async def choose_category(callback: CallbackQuery):
    category_id = callback.data.split(":", 1)[1]
    category = GUIDES[category_id]

    await callback.message.edit_text(
        f"📂 <b>{category['title']}</b>\n\nВыберите нужную инструкцию:",
        reply_markup=category_keyboard(category_id),
    )
    await callback.answer()


# ---------- Показ конкретного гайда ----------
@dp.callback_query(F.data.startswith("guide:"))
async def show_guide(callback: CallbackQuery):
    _, category_id, index_str = callback.data.split(":", 2)
    index = int(index_str)
    guide = GUIDES[category_id]["guide"][index]

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
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
        )
    await callback.answer()


# ---------- Запуск ----------
async def main():
    logging.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
