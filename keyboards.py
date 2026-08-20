
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ---------- Кнопки главного меню (категории) ----------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню со списком категорий гайдов."""
    from guides import GUIDES

    builder = InlineKeyboardBuilder()
    for category_id, category in GUIDES.items():
        builder.button(
            text=category["title"],
            callback_data=f"cat:{category_id}",
        )
    builder.adjust(1)
    return builder.as_markup()


# ---------- Кнопки конкретной категории (список гайдов) ----------
def category_keyboard(category_id: str) -> InlineKeyboardMarkup:
    """Список гайдов внутри категории + кнопка «Назад»."""
    from guides import GUIDES

    builder = InlineKeyboardBuilder()
    for index in range(len(GUIDES[category_id]["guide"])):
        guide = GUIDES[category_id]["guide"][index]
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
    from guides import GUIDES

    builder = InlineKeyboardBuilder()

    if guide.get("url"):
        builder.button(
            text=guide.get("url_label", "🔗 Открыть"),
            url=guide["url"],
        )

    builder.button(
        text="◀️ К списку",
        callback_data=f"cat:{category_id}",
    )
    builder.button(text="🏠 В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()
