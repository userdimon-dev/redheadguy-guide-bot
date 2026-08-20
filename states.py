"""
Состояния мастер-диалогов админ-панели (aiogram FSM).
"""

from aiogram.fsm.state import State, StatesGroup


# Мастер добавления нового гайда
class AddGuideStates(StatesGroup):
    choose_category = State()   # выбор категории
    enter_title = State()       # ввод заголовка
    enter_text = State()        # ввод текста
    enter_url = State()         # ввод ссылки (или пропуск)
    enter_url_label = State()   # ввод подписи к ссылке (или пропуск)
    ask_photo = State()         # загрузка фото (или пропуск)
    ask_show_bot_links = State()# показывать ли кнопки бота/ссылок


# Мастер добавления новой категории
class AddCategoryStates(StatesGroup):
    enter_id = State()          # ввод ID категории (латиницей)
    enter_title = State()       # ввод названия


# Мастер редактирования существующего гайда
# (похож на AddGuideStates, отражает те же шаги, но отдельно)
class EditGuideStates(StatesGroup):
    run = State()               # выполняем шаги мастера (шаг хранится в state)

