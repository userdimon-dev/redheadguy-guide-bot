"""
Telegram-админ-панель управления контентом гайдов.

Доступна только администраторам (см. config.ADMIN_ID).
Реализовано через мастер-диалог (aiogram FSM).
"""

import logging
import os

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import is_admin
from guides import load_guides, save_guides
from keyboards import main_menu_keyboard
from states import AddGuideStates, AddCategoryStates, EditGuideStates

router = Router()
logger = logging.getLogger("admin")


def safe_edit(message, text, **kwargs):
    """
    Безопасное редактирование сообщения.
    Игнорирует ошибку 'message is not modified' (повторное нажатие),
    чтобы не спамить логами и не падать.
    """
    try:
        return message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        # Проверяем и по тексту исключения, и по атрибуту .message
        err = f"{e} {getattr(e, 'message', '')}".lower()
        if "not modified" in err:
            logger.debug("Игнорируем 'message is not modified'")
            return  # контент уже тот же — пропускаем
        raise

# Папка для медиа (скриншоты и т.п.)
MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)


# ---------- Вспомогательные клавиатуры ----------
def admin_menu_keyboard():
    """Главное меню админ-панели."""
    b = InlineKeyboardBuilder()
    b.button(text="➕ Добавить категорию", callback_data="admin:add_category")
    b.button(text="➕ Добавить гайд", callback_data="admin:add_guide")
    b.button(text="📂 Категории и гайды", callback_data="admin:list")
    b.button(text="✏️ Управление гайдами", callback_data="admin:manage")
    b.button(text="🗑️ Удалить категорию", callback_data="admin:del_cat")
    b.button(text="🏠 Выход в меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def del_category_choice_keyboard():
    """Список категорий для удаления."""
    b = InlineKeyboardBuilder()
    guides = load_guides()
    for cid in guides.keys():
        cnt = len(guides[cid]["guide"])
        b.button(text=f"🗑️ {guides[cid]['title']} ({cnt})", callback_data=f"admin:delcat:{cid}")
    b.button(text="◀️ Назад", callback_data="admin:back_menu")
    b.adjust(1)
    return b.as_markup()


def manage_categories_keyboard():
    """Список категорий для управления гайдами."""
    b = InlineKeyboardBuilder()
    guides = load_guides()
    for cid in guides.keys():
        b.button(text=f"📂 {guides[cid]['title']}", callback_data=f"admin:mgmt_cat:{cid}")
    b.button(text="◀️ Назад", callback_data="admin:back_menu")
    b.adjust(1)
    return b.as_markup()


def manage_guides_keyboard(category_id: str):
    """Список гайдов в выбранной категории для управления."""
    b = InlineKeyboardBuilder()
    guides = load_guides()
    for idx, g in enumerate(guides[category_id]["guide"]):
        b.button(text=f"{idx+1}. {g['title']}", callback_data=f"admin:mgmt_guide:{category_id}:{idx}")
    b.button(text="◀️ Назад", callback_data="admin:manage")
    b.adjust(1)
    return b.as_markup()


def manage_guide_actions(category_id: str, index: int):
    """Кнопки действий с конкретным гайдом."""
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Редактировать", callback_data=f"admin:edit:{category_id}:{index}")
    b.button(text="🗑️ Удалить", callback_data=f"admin:del:{category_id}:{index}")
    b.button(text="◀️ Назад", callback_data=f"admin:mgmt_cat:{category_id}")
    b.adjust(1)
    return b.as_markup()


def category_choice_keyboard():
    """Кнопки с категориями для выбора при добавлении гайда."""
    b = InlineKeyboardBuilder()
    guides = load_guides()
    for cid in guides.keys():
        b.button(text=guides[cid]["title"], callback_data=f"admin:catsel:{cid}")
    b.button(text="◀️ Отмена", callback_data="admin:cancel")
    b.adjust(1)
    return b.as_markup()


# ---------- Команда /admin ----------
@router.message(Command("admin"))
async def admin_start(message: Message):
    if not is_admin(message.from_user.id):
        logger.warning("Отказано в доступе к админке пользователю %s", message.from_user.id)
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    logger.info("Админ %s открыл админ-панель", message.from_user.id)
    await message.answer(
        "🔐 <b>Админ-панель RedheadGuy</b>\n\n"
        "Управление контентом гайдов:",
        reply_markup=admin_menu_keyboard(),
    )


# ---------- Главное меню админки ----------
@router.callback_query(F.data == "admin:list")
async def admin_show_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    guides = load_guides()
    if not guides:
        await callback.message.edit_text("📂 Категорий пока нет.")
        return

    text = "📂 <b>Текущий контент:</b>\n\n"
    for cid, cat in guides.items():
        text += f"▪️ <b>{cat['title']}</b> (id: {cid}) — {len(cat['guide'])} гайда\n"
    text += "\nВыберите действие:"

    await safe_edit(callback.message, text, reply_markup=admin_menu_keyboard())
    await callback.answer()


# ---------- Добавление категории ----------
@router.callback_query(F.data == "admin:add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AddCategoryStates.enter_id)
    await safe_edit(
        callback.message,
        "📂 Введите <b>ID категории</b> (латиницей, без пробелов, "
        "например <code>obhod</code>):\n\n"
        "<i>Напишите /cancel чтобы отменить.</i>"
    )
    await callback.answer()


@router.message(AddCategoryStates.enter_id)
async def add_category_id(message: Message, state: FSMContext):
    cid = message.text.strip().lower().replace(" ", "_")
    guides = load_guides()
    if cid in guides:
        await message.answer("❌ Такая категория уже существует. Введите другой ID:")
        return
    await state.update_data(category_id=cid)
    await state.set_state(AddCategoryStates.enter_title)
    await message.answer("Теперь введите <b>название категории</b> (с эмодзи):")


@router.message(AddCategoryStates.enter_title)
async def add_category_title(message: Message, state: FSMContext):
    data = await state.get_data()
    cid = data["category_id"]
    title = message.text.strip()

    guides = load_guides()
    guides[cid] = {"title": title, "guide": []}
    save_guides(guides)
    logger.info("Админ %s создал категорию %s (%s)", message.from_user.id, title, cid)

    await state.clear()
    await message.answer(f"✅ Категория <b>{title}</b> создана!", reply_markup=admin_menu_keyboard())


# ---------- Добавление гайда: выбор категории ----------
@router.callback_query(F.data == "admin:add_guide")
async def add_guide_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    guides = load_guides()
    if not guides:
        await safe_edit(
            callback.message,
            "❌ Сначала создайте категорию.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    await state.set_state(AddGuideStates.choose_category)
    await safe_edit(
        callback.message,
        "Выберите категорию для нового гайда:",
        reply_markup=category_choice_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:catsel:"))
async def guide_category_selected(callback: CallbackQuery, state: FSMContext):
    cid = callback.data.split(":", 2)[2]
    await state.update_data(category_id=cid)
    await state.set_state(AddGuideStates.enter_title)
    await safe_edit(
        callback.message,
        "Введите <b>заголовок</b> нового гайда (например, "
        "<i>🖥️ Как подключиться на Windows</i>):"
    )
    await callback.answer()


# ---------- Ввод текста гайда ----------
@router.message(AddGuideStates.enter_title)
async def guide_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddGuideStates.enter_text)
    await message.answer(
        "Введите <b>текст гайда</b>. Можно использовать HTML-разметку\n"
        "(<code>&lt;b&gt;</code>, <code>&lt;a href&gt;</code>, <code>&lt;code&gt;</code> и т.д.).\n"
        "Новый гайд можно разбивать на строки."
    )


@router.message(AddGuideStates.enter_text)
async def guide_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Пропустить", callback_data="admin:skip_url")
    kb.button(text="◀️ Ввести ссылку", callback_data="admin:no_skip_url")
    await state.set_state(AddGuideStates.enter_url)
    await message.answer(
        "Есть ли <b>ссылка/кнопка</b> для этого гайда? "
        "(например, ссылка на скачивание)",
        reply_markup=kb.as_markup(),
    )


# ---------- Обработка ссылки ----------
@router.callback_query(F.data == "admin:skip_url", AddGuideStates.enter_url)
async def guide_skip_url(callback: CallbackQuery, state: FSMContext):
    await state.update_data(url=None, url_label=None)
    await _ask_photo(callback.message, state)
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "admin:no_skip_url", AddGuideStates.enter_url)
async def guide_no_skip_url(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddGuideStates.enter_url)
    await safe_edit(callback.message, "Введите саму ссылку (URL):")
    await callback.answer()


@router.message(AddGuideStates.enter_url)
async def guide_url(message: Message, state: FSMContext):
    await state.update_data(url=message.text.strip())
    await state.set_state(AddGuideStates.enter_url_label)
    await message.answer("Введите <b>подпись</b> кнопки (например, «⬇️ Скачать»):")


@router.message(AddGuideStates.enter_url_label)
async def guide_url_label(message: Message, state: FSMContext):
    await state.update_data(url_label=message.text.strip())
    await _ask_photo(message, state)


# ---------- Спросить про фото ----------
async def _ask_photo(message: Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ Без фото", callback_data="admin:no_photo")
    await state.set_state(AddGuideStates.ask_photo)
    await message.answer(
        "📸 Прикрепите <b>скриншот/инструкцию</b> для гайда, "
        "или нажмите «Без фото»:",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "admin:no_photo", AddGuideStates.ask_photo)
async def guide_no_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    await _ask_show_bot_links(callback.message, state)
    await callback.message.delete()
    await callback.answer()


@router.message(AddGuideStates.ask_photo, F.photo)
async def guide_photo(message: Message, state: FSMContext, bot):
    folder = os.path.join(MEDIA_DIR, "photos")
    os.makedirs(folder, exist_ok=True)

    # Самый большой размер фото
    photo = message.photo[-1]
    # Скачиваем файл в media/photos
    dest = os.path.join(folder, f"{photo.file_unique_id}.jpg")
    await bot.download(photo.file_id, destination=dest)

    # Сохраняем относительный путь к файлу
    await state.update_data(photo=os.path.join("media", "photos", f"{photo.file_unique_id}.jpg"))
    await _ask_show_bot_links(message, state)


# ---------- Показывать ли кнопки бота ----------
async def _ask_show_bot_links(message: Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="admin:botlinks:yes")
    kb.button(text="❌ Нет", callback_data="admin:botlinks:no")
    await state.set_state(AddGuideStates.ask_show_bot_links)
    await message.answer(
        "Показывать ли кнопки основного бота и доп.ссылок в этом гайде?",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data.startswith("admin:botlinks:"))
async def guide_botlinks(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 2)[2] == "yes"
    await state.update_data(show_bot_links=value)

    # Достаём все данные и сохраняем гайд
    data = await state.get_data()
    guides = load_guides()
    cid = data["category_id"]

    new_guide = {
        "title": data["title"],
        "text": data["text"],
    }
    if data.get("url"):
        new_guide["url"] = data["url"]
        new_guide["url_label"] = data.get("url_label", "🔗 Перейти")
    if data.get("photo"):
        new_guide["photo"] = data["photo"]
    if data.get("show_bot_links"):
        new_guide["show_bot_links"] = True

    guides[cid]["guide"].append(new_guide)
    save_guides(guides)
    logger.info(
        "Админ %s добавил гайд «%s» в категорию %s",
        callback.from_user.id, data["title"], cid,
    )

    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "✅ <b>Гайд добавлен!</b>",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


# ---------- Управление гайдами: меню выбора категории ----------
@router.callback_query(F.data == "admin:manage")
async def manage_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    guides = load_guides()
    if not guides:
        await safe_edit(callback.message, "📂 Категорий пока нет.", reply_markup=admin_menu_keyboard())
        return
    await safe_edit(
        callback.message,
        "Выберите категорию для управления гайдами:",
        reply_markup=manage_categories_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:back_menu")
async def manage_back_menu(callback: CallbackQuery):
    await safe_edit(
        callback.message,
        "🔐 <b>Админ-панель RedheadGuy</b>\n\nУправление контентом гайдов:",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:mgmt_cat:"))
async def manage_category_chosen(callback: CallbackQuery):
    cid = callback.data.split(":", 2)[2]
    await safe_edit(
        callback.message,
        "Выберите гайд для редактирования/удаления:",
        reply_markup=manage_guides_keyboard(cid),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:mgmt_guide:"))
async def manage_guide_chosen(callback: CallbackQuery):
    _, _, cid, idx_str = callback.data.split(":")
    idx = int(idx_str)
    guides = load_guides()
    g = guides[cid]["guide"][idx]
    await safe_edit(
        callback.message,
        f"🛠️ <b>{g['title']}</b>\n\nВыберите действие:",
        reply_markup=manage_guide_actions(cid, idx),
    )
    await callback.answer()


# ---------- Удаление гайда (с подтверждением) ----------
@router.callback_query(F.data.startswith("admin:del:"))
async def delete_guide_confirm(callback: CallbackQuery):
    _, _, cid, idx_str = callback.data.split(":")
    idx = int(idx_str)
    guides = load_guides()
    g = guides[cid]["guide"][idx]

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, удалить", callback_data=f"admin:del_yes:{cid}:{idx}")
    kb.button(text="❌ Нет", callback_data=f"admin:mgmt_guide:{cid}:{idx}")
    kb.adjust(2)
    await safe_edit(
        callback.message,
        f"⚠️ Удалить гайд <b>«{g['title']}»</b>?",
        reply_markup=kb.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:del_yes:"))
async def delete_guide_done(callback: CallbackQuery):
    _, _, cid, idx_str = callback.data.split(":")
    idx = int(idx_str)
    guides = load_guides()
    removed = guides[cid]["guide"].pop(idx)
    save_guides(guides)
    logger.info("Админ %s удалил гайд «%s»", callback.from_user.id, removed.get("title"))

    await safe_edit(
        callback.message,
        f"🗑️ Гайд <b>«{removed.get('title')}»</b> удалён.",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


# ---------- Редактирование гайда: начало мастера ----------
@router.callback_query(F.data.startswith("admin:edit:"))
async def edit_guide_start(callback: CallbackQuery, state: FSMContext):
    _, _, cid, idx_str = callback.data.split(":")
    idx = int(idx_str)
    guides = load_guides()
    g = guides[cid]["guide"][idx]

    # Сохраняем контекст редактирования
    await state.update_data(edit_category=cid, edit_index=idx)
    await state.set_state(EditGuideStates.run)
    # Шаг 1: заголовок
    await state.update_data(edit_step="title", edit_title=g.get("title", ""))
    await safe_edit(
        callback.message,
        "✏️ <b>Редактирование гайда</b>\n\n"
        f"Текущий заголовок: <b>{g.get('title','')}</b>\n\n"
        "Введите новый заголовок (или <code>/skip</code> — оставить без изменений):",
    )
    await callback.answer()


@router.message(EditGuideStates.run)
async def edit_guide_process(message: Message, state: FSMContext):
    data = await state.get_data()
    step = data.get("edit_step")
    cid = data["edit_category"]
    idx = data["edit_index"]
    guides = load_guides()
    g = guides[cid]["guide"][idx]

    text = message.text.strip()
    skip = text.lower() == "/skip"

    if step == "title":
        if not skip:
            g["title"] = text
        await state.update_data(edit_step="text")
        await message.answer(
            f"Текущий текст гайда:\n<pre>{g.get('text','')[:300]}</pre>\n\n"
            "Введите новый текст (или <code>/skip</code>):"
        )

    elif step == "text":
        if not skip:
            g["text"] = text
        await state.update_data(edit_step="url")
        kb = InlineKeyboardBuilder()
        kb.button(text="⏭️ Оставить ссылку как есть", callback_data="admin:edit_keep_url")
        kb.button(text="✏️ Изменить ссылку", callback_data="admin:edit_change_url")
        kb.button(text="🗑️ Убрать ссылку", callback_data="admin:edit_remove_url")
        await message.answer(
            "Ссылка сейчас: "
            + (f"<code>{g.get('url','')}</code>" if g.get("url") else "<i>нет</i>")
            + "\n\nЧто сделать со ссылкой?",
            reply_markup=kb.as_markup(),
        )

    elif step == "new_url":
        # Пользователь ввёл новую ссылку; запрашиваем подпись
        if not skip:
            g["url"] = text
        await state.update_data(edit_step="url_label")
        await message.answer("Введите <b>подпись</b> для ссылки (или <code>/skip</code>):")

    elif step == "url_label":
        if not skip:
            g["url_label"] = text
        await _finish_edit(message, state)

    # На каждом шаге сохраняем текущее состояние гайда
    save_guides(guides)


async def _finish_edit(message, state: FSMContext):
    data = await state.get_data()
    cid = data["edit_category"]
    guides = load_guides()
    g = guides[cid]["guide"][data["edit_index"]]
    logger.info(
        "Админ %s отредактировал гайд «%s»",
        message.from_user.id if hasattr(message, "from_user") else "?",
        g.get("title", ""),
    )
    await state.clear()
    await message.answer(
        f"✅ Гайд <b>«{g.get('title','')}»</b> обновлён!",
        reply_markup=admin_menu_keyboard(),
    )


# ---------- Редактирование ссылки ----------
@router.callback_query(F.data == "admin:edit_keep_url", EditGuideStates.run)
async def edit_keep_url(callback: CallbackQuery, state: FSMContext):
    await _finish_edit(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "admin:edit_remove_url", EditGuideStates.run)
async def edit_remove_url(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cid = data["edit_category"]
    idx = data["edit_index"]
    guides = load_guides()
    g = guides[cid]["guide"][idx]
    g.pop("url", None)
    g.pop("url_label", None)
    save_guides(guides)
    await _finish_edit(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "admin:edit_change_url", EditGuideStates.run)
async def edit_change_url(callback: CallbackQuery, state: FSMContext):
    await state.update_data(edit_step="new_url")
    await safe_edit(callback.message, "Введите новую ссылку (URL):")
    await callback.answer()


# ---------- Удаление категории ----------
@router.callback_query(F.data == "admin:del_cat")
async def delete_category_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    guides = load_guides()
    if not guides:
        await safe_edit(callback.message, "📂 Категорий пока нет.", reply_markup=admin_menu_keyboard())
        return
    await safe_edit(
        callback.message,
        "Выберите категорию для удаления:\n\n"
        "<i>Внимание: будут удалены все гайды внутри неё.</i>",
        reply_markup=del_category_choice_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:delcat:"))
async def delete_category_confirm(callback: CallbackQuery):
    cid = callback.data.split(":", 2)[2]
    guides = load_guides()
    cat = guides.get(cid)
    if not cat:
        await safe_edit(callback.message, "❌ Категория не найдена.", reply_markup=admin_menu_keyboard())
        return

    cnt = len(cat["guide"])
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, удалить", callback_data=f"admin:delcat_yes:{cid}")
    kb.button(text="❌ Нет", callback_data="admin:back_menu")
    kb.adjust(2)
    await safe_edit(
        callback.message,
        f"⚠️ Удалить категорию <b>«{cat['title']}»</b> "
        f"вместе с {cnt} гайдами?",
        reply_markup=kb.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:delcat_yes:"))
async def delete_category_done(callback: CallbackQuery):
    cid = callback.data.split(":", 2)[2]
    guides = load_guides()
    removed = guides.pop(cid, None)
    save_guides(guides)
    if removed:
        logger.info(
            "Админ %s удалил категорию %s (%s)",
            callback.from_user.id, removed.get("title"), cid,
        )
        await safe_edit(
            callback.message,
            f"🗑️ Категория <b>«{removed.get('title')}»</b> удалена.",
            reply_markup=admin_menu_keyboard(),
        )
    else:
        await safe_edit(
            callback.message,
            "❌ Категория не найдена.",
            reply_markup=admin_menu_keyboard(),
        )
    await callback.answer()


# ---------- Отмена ----------
@router.callback_query(F.data == "admin:cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(
        callback.message,
        "❌ Действие отменено.",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено.")
