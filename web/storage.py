"""
Работа с контентом гайдов для веб-редактора.
Читает/пишет тот же data/guides.json, что и бот.
"""

import json
import os
from datetime import datetime

from .config import DATA_DIR, GUIDES_FILE, USERS_FILE

BACKUP_DIR = os.path.join(DATA_DIR, "backups")


def load_guides() -> dict:
    if not os.path.exists(GUIDES_FILE):
        return {}
    try:
        with open(GUIDES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_guides(guides: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = GUIDES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(guides, f, ensure_ascii=False, indent=2)
    os.replace(tmp, GUIDES_FILE)  # атомарная запись


def backup_guides() -> str | None:
    """Создаёт резервную копию guides.json. Возвращает путь к бэкапу или None."""
    if not os.path.exists(GUIDES_FILE):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"guides_{stamp}.json")
    try:
        with open(GUIDES_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        return dst
    except OSError:
        return None


def count_stats():
    """Возвращает счётчики: категории, гайды, пользователей."""
    guides = load_guides()

    total_cats = len(guides)
    total_guides = 0
    for cat in guides.values():
        total_guides += len(cat.get("guide", []))

    users = 0
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = len(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass

    return {"categories": total_cats, "guides": total_guides, "users": users}
