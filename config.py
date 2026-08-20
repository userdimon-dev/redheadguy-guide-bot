"""
Конфигурация бота.
Все настройки читаются из переменных окружения или файла .env
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# ---------- Токен бота (обязательно) ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# ---------- Ссылки (опционально, настраиваются через .env) ----------
# Основной бот — всегда нужен (если не задан, кнопка использует дефолтную ссылку)
MAIN_BOT_URL = os.getenv("MAIN_BOT_URL", "https://t.me/redheadguy_bot")

# Дополнительные ссылки (если заданы в .env — выводим кнопки, если нет — пропускаем)
CHANNEL_URL = os.getenv("CHANNEL_URL", "")   # канал новостей
CABINET_URL = os.getenv("CABINET_URL", "")   # личный кабинет
SUPPORT_URL = os.getenv("SUPPORT_URL", "")   # поддержка
SITE_URL    = os.getenv("SITE_URL", "")      # официальный сайт


def get_extra_links() -> list[tuple[str, str]]:
    """
    Возвращает список дополнительных ссылок в формате (метка, URL).
    Пустые/пустые ссылки пропускаются. Основной бот сюда НЕ входит.
    """
    links = []
    if CHANNEL_URL:
        links.append(("📢 Канал новостей", CHANNEL_URL))
    if CABINET_URL:
        links.append(("👤 Личный кабинет", CABINET_URL))
    if SUPPORT_URL:
        links.append(("💬 Поддержка", SUPPORT_URL))
    if SITE_URL:
        links.append(("🌐 Сайт", SITE_URL))
    return links
