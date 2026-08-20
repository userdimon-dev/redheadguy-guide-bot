from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MAIN_BOT_URL, get_extra_links
from guides import load_guides


# ---------- Кнопки главного меню (категории) ----------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню со списком категорий гайдов + кнопка поиска."""
    guides = load_guides()

    builder = InlineKeyboardBuilder()
    for category_id, category in guides.items():
        builder.button(
            text=category["title"],
            callback_data=f"cat:{category_id}",
        )
    builder.button(text="🔍 Поиск", callback_data="search")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Кнопки конкретной категории (список гайдов) ----------
def category_keyboard(category_id: str) -> InlineKeyboardMarkup:
    """Список гайдов внутри категории + кнопка «Назад»."""
    guides = load_guides()

    builder = InlineKeyboardBuilder()
    for index in range(len(guides[category_id]["guide"])):
        guide = guides[category_id]["guide"][index]
        builder.button(
            text=guide["title"],
            callback_data=f"guide:{category_id}:{index}",
        )
    builder.button(text="◀️ Назад", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Кнопки внутри конкретного гайда ----------
def guide_keyboard(category_id: str, index: int, guide: dict) -> InlineKeyboardMarkup:
    """Кнопки для показанного гайда: ссылка (если есть) + навигация."""
    builder = InlineKeyboardBuilder()

    # 1. Обычная ссылка гайда (если задана)
    if guide.get("url"):
        builder.button(
            text=guide.get("url_label", "🔗 Открыть"),
            url=guide["url"],
        )

    # 2. Если гайд помечен show_bot_links — добавляем кнопку основного бота
    #    и доп. ссылки (канал, кабинет и т.д.) из конфига (.env)
    if guide.get("show_bot_links"):
        # Кнопка на основной бот
        builder.button(
            text="🤖 Перейти в основной бот",
            url=MAIN_BOT_URL,
        )
        # Дополнительные ссылки из .env (если заданы)
        for label, url in get_extra_links():
            builder.button(text=label, url=url)

    # 3. Навигация
    builder.button(
        text="◀️ К списку",
        callback_data=f"cat:{category_id}",
    )
    builder.button(text="🏠 В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()

