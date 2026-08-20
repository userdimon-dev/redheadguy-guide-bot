
"""
Модуль доступа к гайдам.

Гайды хранятся в JSON-файле (data/guides.json) и редактируются
через Telegram-админ-панель (или вручную в файле).
"""

import json
import os

# Путь к файлу с контентом
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GUIDES_FILE = os.path.join(DATA_DIR, "guides.json")


def load_guides() -> dict:
    """Загружает словарь гайдов из JSON-файла."""
    if not os.path.exists(GUIDES_FILE):
        return {}
    with open(GUIDES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_guides(guides: dict) -> None:
    """Сохраняет словарь гайдов в JSON-файл."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GUIDES_FILE, "w", encoding="utf-8") as f:
        json.dump(guides, f, ensure_ascii=False, indent=2)


# Актуальный срез гайдов для использования в боте (загружается при старте)
GUIDES = load_guides()
