# 🤖 RedheadGuy Guide Bot

Telegram-бот с гайдами по настройкам, подключению и сервисам RedheadGuy.
Работает на **aiogram 3** (Python).

## ✨ Возможности
- 📱 Пошаговые гайды по настройке приложений (Happ, Incy и др.)
- 🖥️ Инструкции для разных устройств (Windows, Android, iOS, Linux)
- 🔗 Кнопки с полезными ссылками
- 🖼️ Поддержка картинок-инструкций
- 📂 Лёгкое добавление новых гайдов

## 🚀 Установка и запуск

### Вариант А: Docker Compose (рекомендуется для сервера)
```bash
docker compose up -d --build
```
Останавливает:
```bash
docker compose down
```
Логи:
```bash
docker compose logs -f bot
```

### Вариант Б: Без Docker (для разработки локально)
```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Настройте .env (см. ниже)

# 3. Запустите
python bot.py
```

## ⚙️ Настройка (.env)
Скопируйте `.env.example` в `.env` и заполните:
```bash
cp .env.example .env
nano .env
```
Минимально достаточно токена. Все ссылки настраиваются там же.

## 📂 Как добавить новый гайд
(Появится админ-панель в Telegram — скоро.)
Или вручную: откройте `guides.py` и добавьте категорию/гайд по шаблону.

## 🗂️ Структура проекта
```
redheadguy-guide-bot/
├── bot.py               # главный файл (логика бота)
├── config.py            # настройки / токен / ссылки
├── guides.py            # все гайды (контент)
├── keyboards.py         # клавиатуры
├── Dockerfile           # сборка образа
├── docker-compose.yml   # оркестрация (Docker Compose)
├── requirements.txt     # зависимости
├── .env                 # токен и настройки (не коммитить!)
├── .env.example         # шаблон настроек
└── README.md
```
