# Образ Python
FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости отдельно (для кэширования слоёв)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY . .

# Команда запуска
CMD ["python", "bot.py"]
