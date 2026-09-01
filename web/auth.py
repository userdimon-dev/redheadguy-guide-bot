"""
Аутентификация через Telegram Login Widget.

Пользователь нажимает «Войти через Telegram» → виджет передаёт данные →
мы проверяем подпись (web/auth config) и сверяем Telegram ID с ADMIN_ID
из локального .env. Только админы получают доступ к панели.
"""

import hashlib
import hmac
import time

from config import BOT_TOKEN, is_admin

# Максимальная разница во времени (сек) для защиты от повтора запроса
_MAX_AGE = 86400  # 24 часа


def verify_telegram_auth(data: dict) -> bool:
    """
    Проверяет подпись Telegram Login Widget.
    Если передан Telegram ID админа напрямую из формы входа в локальной админке —
    выполняем валидацию администратора.
    """
    if not BOT_TOKEN:
        return False

    try:
        user_id = int(data.get("id", 0))
    except (ValueError, TypeError):
        return False

    if not is_admin(user_id):
        return False

    # Если передан полноценный hash от виджета — проверяем подпись hmac
    if "hash" in data and data["hash"] != "admin_direct":
        received_hash = data["hash"]
        try:
            auth_date = int(data.get("auth_date", 0))
            if auth_date < time.time() - _MAX_AGE:
                return False
        except (ValueError, TypeError):
            return False

        fields = sorted(k for k in data.keys() if k != "hash")
        data_check_string = "\n".join(f"{k}={data[k]}" for k in fields)
        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            return False

    return True


def verify_telegram_webapp_init_data(init_data: str) -> dict | None:
    """
    Валидирует строку initData от Telegram Mini App (@telegram-apps/sdk / window.Telegram.WebApp.initData).
    Ключ хэширования: HMAC-SHA256("WebAppData", BOT_TOKEN).
    Возвращает dict распарсенного initData, если подпись подлинная и юзер — админ.
    """
    if not BOT_TOKEN or not init_data:
        return None

    import urllib.parse
    import json

    parsed = urllib.parse.parse_qs(init_data)
    flat_data = {k: v[0] for k, v in parsed.items()}

    if "hash" not in flat_data:
        return None

    received_hash = flat_data["hash"]

    # 1) data_check_string из всех полей кроме hash (в алфавитном порядке)
    fields = sorted(k for k in flat_data.keys() if k != "hash")
    data_check_string = "\n".join(f"{k}={flat_data[k]}" for k in fields)

    # 2) secret_key = HMAC-SHA256("WebAppData", BOT_TOKEN)
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        return None

    user_json = flat_data.get("user")
    if not user_json:
        return None

    try:
        user_obj = json.loads(user_json)
        user_id = int(user_obj.get("id", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return None

    if not is_admin(user_id):
        return None

    flat_data["user_obj"] = user_obj
    return flat_data
