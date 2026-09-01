"""
Хранение зарегистрированных пользователей бота (их Telegram ID).
Используется для уведомлений о новых пользователях и аналитики.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


def _load_users() -> set[int]:
    """Загружает список известных пользователей из файла."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()
    except (json.JSONDecodeError, OSError):
        return set()


def _save_users(users: set[int]) -> None:
    """Сохраняет список пользователей в файл."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(users), f, ensure_ascii=False)
    except OSError:
        pass


DISCLAIMERS_FILE = os.path.join(DATA_DIR, "disclaimers.json")


def has_accepted_disclaimer(user_id: int) -> bool:
    """Проверяет, принял ли пользователь дисклеймер."""
    try:
        if not os.path.exists(DISCLAIMERS_FILE):
            return False
        with open(DISCLAIMERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return user_id in data
    except Exception:
        return False


def set_accepted_disclaimer(user_id: int) -> None:
    """Отмечает, что пользователь принял дисклеймер."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        accepted = set()
        if os.path.exists(DISCLAIMERS_FILE):
            with open(DISCLAIMERS_FILE, "r", encoding="utf-8") as f:
                accepted = set(json.load(f))
        accepted.add(user_id)
        with open(DISCLAIMERS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(accepted), f, ensure_ascii=False)
    except Exception:
        pass


def register_user(user_id: int) -> bool:
    """
    Регистрирует пользователя. Возвращает True, если пользователь НОВЫЙ
    (его ещё не было в списке), иначе False.
    """
    if user_id <= 0:
        return False
    users = _load_users()
    if user_id in users:
        return False
    users.add(user_id)
    _save_users(users)
    return True


def count_users() -> int:
    """Возвращает общее число зарегистрированных пользователей."""
    return len(_load_users())
