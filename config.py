"""
Конфигурация бота.
Все настройки читаются из переменных окружения или файла .env
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# ---------- Версия бота ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")


def get_version() -> str:
    """Возвращает текущую версию бота из файла VERSION."""
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "unknown"

BOT_VERSION = get_version()
BOT_NAME = "RedHeadGuy Guide Bot"

# ---------- Токен бота (обязательно) ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# ---------- Админ (обязательно для админ-панели) ----------
# Telegram ID администратора, который может управлять контентом.
# Можно указать несколько ID через запятую: ADMIN_ID=294323949,123456789
ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли user_id администратором."""
    return user_id in ADMIN_ID

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

