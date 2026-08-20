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
    data — dict из query-string виджета (id, first_name, auth_date, hash).
    Возвращает True, если подпись валидна, данные свежие и пользователь админ.
    """
    if not BOT_TOKEN or "hash" not in data:
        return False

    received_hash = data["hash"]

    # 1) Проверяем «свежесть» данных
    try:
        auth_date = int(data.get("auth_date", 0))
    except (ValueError, TypeError):
        return False
    if auth_date < time.time() - _MAX_AGE:
        return False

    # 2) Собираем data_check_string (ключи в алфавитном порядке)
    fields = sorted(k for k in data.keys() if k != "hash")
    data_check_string = "\n".join(f"{k}={data[k]}" for k in fields)

    # 3) secret_key = SHA256(bot_token)
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # 4) Сравниваем подпись
    if not hmac.compare_digest(calculated, received_hash):
        return False

    # 5) Проверяем, что Telegram ID является админом
    try:
        user_id = int(data.get("id", 0))
    except (ValueError, TypeError):
        return False
    return is_admin(user_id)
