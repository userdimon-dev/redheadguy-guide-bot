from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    MAIN_BOT_URL,
    WEB_APP_URL,
    WEB_APP_BUTTON_TEXT,
    ENABLE_MINI_APP,
    DISCLAIMER_BUTTON_TEXT,
    get_extra_links,
)
from guides import load_guides


# ---------- Дисклеймер ----------
def disclaimer_keyboard() -> InlineKeyboardMarkup:
    """Кнопка подтверждения согласия с дисклеймером."""
    builder = InlineKeyboardBuilder()
    builder.button(text=DISCLAIMER_BUTTON_TEXT, callback_data="accept_disclaimer")
    return builder.as_markup()


# ---------- Кнопки главного меню (категории) ----------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню со списком видимых категорий гайдов + кнопка поиска.
    Кнопки группируются по row_number и сортируются по sort_order."""
    guides = load_guides()

    # Фильтруем скрытые категории
    visible_cats = [
        (cat_id, cat)
        for cat_id, cat in guides.items()
        if not cat.get("is_hidden", False)
    ]
    # Сортируем по sort_order
    visible_cats.sort(key=lambda x: (x[1].get("sort_order", 0), x[0]))

    # Группируем по row_number
    rows_map = {}
    for cat_id, cat in visible_cats:
        r_num = cat.get("row_number", 1)
        rows_map.setdefault(r_num, []).append((cat["title"], f"cat:{cat_id}"))

    builder = InlineKeyboardBuilder()
    sorted_row_keys = sorted(rows_map.keys())
    row_sizes = []
    for r_num in sorted_row_keys:
        buttons = rows_map[r_num]
        for text, cb_data in buttons:
            builder.button(text=text, callback_data=cb_data)
        row_sizes.append(len(buttons))

    if row_sizes:
        builder.adjust(*row_sizes)

    # Если включен Mini App — добавляем кнопку вызова WebApp
    if ENABLE_MINI_APP and WEB_APP_URL:
        webapp_builder = InlineKeyboardBuilder()
        webapp_builder.button(
            text=WEB_APP_BUTTON_TEXT,
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
        builder.attach(webapp_builder)

    # Кнопку поиска добавляем отдельным рядом
    search_builder = InlineKeyboardBuilder()
    search_builder.button(text="🔍 Поиск", callback_data="search")
    builder.attach(search_builder)

    return builder.as_markup()


# ---------- Кнопки конкретной категории (список гайдов) ----------
def category_keyboard(category_id: str) -> InlineKeyboardMarkup:
    """Список видимых гайдов внутри категории + кнопка «Назад».
    Кнопки группируются по row_number и сортируются по sort_order."""
    guides = load_guides()
    cat_data = guides.get(category_id, {})
    all_guides = cat_data.get("guide", [])

    # Собираем видимые гайды с их реальным оригинальным индексом
    visible_guides = [
        (idx, g)
        for idx, g in enumerate(all_guides)
        if not g.get("is_hidden", False)
    ]
    # Сортируем по sort_order
    visible_guides.sort(key=lambda x: (x[1].get("sort_order", 0), x[0]))

    rows_map = {}
    for orig_idx, g in visible_guides:
        r_num = g.get("row_number", 1)
        rows_map.setdefault(r_num, []).append((g["title"], f"guide:{category_id}:{orig_idx}"))

    builder = InlineKeyboardBuilder()
    sorted_row_keys = sorted(rows_map.keys())
    row_sizes = []
    for r_num in sorted_row_keys:
        buttons = rows_map[r_num]
        for text, cb_data in buttons:
            builder.button(text=text, callback_data=cb_data)
        row_sizes.append(len(buttons))

    if row_sizes:
        builder.adjust(*row_sizes)

    # Кнопку «Назад» добавляем отдельным рядом
    back_builder = InlineKeyboardBuilder()
    back_builder.button(text="◀️ Назад", callback_data="menu")
    builder.attach(back_builder)

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

