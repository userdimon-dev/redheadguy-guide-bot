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

BOT_VERSION = "2.0.0"
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

# ---------- Ссылки и Настройки Веб-панели ----------
BOT_USERNAME = os.getenv("BOT_USERNAME", "redheadguy_bot")
WEB_SITE_NAME = os.getenv("WEB_SITE_NAME", "RedheadGuy Admin")

MAIN_BOT_URL = os.getenv("MAIN_BOT_URL", "https://t.me/redheadguy_bot")
CHANNEL_URL = os.getenv("CHANNEL_URL", "")   # канал новостей
CABINET_URL = os.getenv("CABINET_URL", "")   # личный кабинет
SUPPORT_URL = os.getenv("SUPPORT_URL", "")   # поддержка
SITE_URL    = os.getenv("SITE_URL", "")      # официальный сайт

# ---------- Telegram Mini App & Web Panel ----------
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://redheadguide.redheadguy.ru")
WEB_APP_BUTTON_TEXT = os.getenv("WEB_APP_BUTTON_TEXT", "🚀 Открыть базу знаний")
ENABLE_MINI_APP = os.getenv("ENABLE_MINI_APP", "true").lower() in ("true", "1", "yes")

# ---------- Onboarding & Disclaimer ----------
ENABLE_DISCLAIMER = os.getenv("ENABLE_DISCLAIMER", "true").lower() in ("true", "1", "yes")
DISCLAIMER_TEXT = os.getenv("DISCLAIMER_TEXT", "Добро пожаловать в RedheadGuy Guide Bot! Данный ресурс носит ознакомительный характер.")
DISCLAIMER_BUTTON_TEXT = os.getenv("DISCLAIMER_BUTTON_TEXT", "✅ Принять и продолжить")

# ---------- Custom Branding ----------
BRAND_NAME = os.getenv("BRAND_NAME", "REDHEADGUY PRIVATE")
DEFAULT_LOGO_PATH = os.getenv("DEFAULT_LOGO_PATH", "media/logo.png")


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

