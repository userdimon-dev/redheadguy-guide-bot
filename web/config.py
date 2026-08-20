"""
Настройки веб-редактора.

Переиспользует корневые настройки (BOT_TOKEN, is_admin) из config.py
и добавляет веб-специфичные переменные (SITE_NAME, BOT_USERNAME).
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения (.env в корне проекта)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Переиспользуем корневые настройки бота
from config import BOT_TOKEN, ADMIN_ID, is_admin  # noqa: E402

# Название сайта / домен для шапки
SITE_NAME = os.getenv("WEB_SITE_NAME", "RedheadGuy Admin")
# Имя пользователя бота (без @) — для виджета «Войти через Telegram»
BOT_USERNAME = os.getenv("BOT_USERNAME", "redheadguy_bot")

# Пути к данным (общие с ботом)
DATA_DIR = os.path.join(BASE_DIR, "data")
GUIDES_FILE = os.path.join(DATA_DIR, "guides.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ANALYTICS_FILE = os.path.join(BASE_DIR, "logs", "analytics.log")
