"""
Централизованная настройка логирования.

Логи пишутся:
  1. В консоль (stdout) — их видно через `docker compose logs`
  2. В файл logs/bot.log — для долговременного хранения
"""

import logging
import os

# Автоперезаписываем конфигурацию логгера один раз при импорте
_configured = False

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    # Создаём корневой логгер
    root_logger = logging.getLogger()
    # Если уже есть обработчики — не дублируем
    if root_logger.handlers:
        return

    root_logger.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # --- 1. Консоль (stdout) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- 2. Файл логов ---
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:  # если файл открыть не удалось — не падаем
        console_handler.stream.write(f"[logger] Не удалось настроить файловый лог: {e}\n")


# Настраиваем логирование при импорте
setup_logging()
