"""
Конфигурация бота.
Токен читается из переменной окружения BOT_TOKEN или файла .env
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Токен бота (создайте в @BotFather и укажите в файле .env)
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
