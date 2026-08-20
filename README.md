# 🤖 RedheadGuy Guide Bot

![Version](https://img.shields.io/badge/version-1.3.1-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-0d8b9b?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

**Telegram-бот с пошаговыми гайдами** по настройке приложений, подключению к сервисам
и рекомендациям RedheadGuy. Работает на **aiogram 3** (Python 3), деплой через **Docker Compose**.

Бот позволяет опубликовать структурированные инструкции (с текстом, картинками и кнопками-ссылками)
и управлять ими прямо из Telegram через встроенную **админ-панель** — без правки кода.

---

## ✨ Возможности

- 📱 Пошаговые гайды по настройке приложений и сервисов
- 🖥️ Инструкции для разных устройств (Windows, Android, iOS, Linux)
- 🔍 Поиск по гайдам (по названию и тексту)
- 🔗 Кнопки с полезными ссылками (основной бот, канал, кабинет, сайт, поддержка)
- 🖼️ Поддержка картинок-инструкций (скриншотов)
- 📂 Контент в **JSON** — редактируется через админку, отдельно от кода
- 🔐 **Telegram-админ-панель** — добавление, редактирование и удаление гайдов и категорий
- 🌐 **Веб-редактор (FastAPI)** — полноценная панель управления через браузер:
  - 🔑 вход через Telegram Login Widget,
  - ✍️ rich text редактор (TinyMCE),
  - 🖱️ drag-and-drop сортировка категорий и гайдов,
  - 👁️ живое превью гайда, 📊 счётчики и поиск
- 📊 **Аналитика** действий пользователей (какие гайды смотрят)
- 📊 **Dashboard статистики** прямо в админке
- 🔔 **Уведомления** админу о новых пользователях
- 📦 **Экспорт/импорт контента** (бэкапы, перенос между ботами)
- 📝 Логирование (консоль + файл + аналитика)
- 🛡️ Обработка ошибок и защита от двойных нажатий
- 🏷️ Версионирование (`/version`, `/about`)

---

## 🚀 Установка из репозитория

### Требования
- **Docker** + **Docker Compose** (рекомендуется для сервера) — либо Python 3.10+
- **Bot token** от [@BotFather](https://t.me/BotFather)

### Вариант А: Docker Compose (рекомендуется для сервера)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/userdimon-dev/redheadguy-guide-bot.git
cd redheadguy-guide-bot

# 2. Настройте окружение
cp .env.example .env
nano .env          # впишите BOT_TOKEN и ADMIN_ID

# 3. Запустите
docker compose up -d --build
```

Остановить бота:

```bash
docker compose down
```

Посмотреть логи в реальном времени:

```bash
docker compose logs -f bot
```

> ⚠️ Контент гайдов хранится в `data/guides.json` и монтируется как volume —
> правки через админку сохраняются даже после пересборки контейнера.

> 🚀 После `docker compose up -d --build` запустятся **и бот, и веб-редактор**.
> Веб-редактор будет доступен на `http://ваш-сервер:8000`.

### Вариант Б: Без Docker (для разработки)

```bash
# 1. Клонируйте и перейдите в папку
git clone https://github.com/userdimon-dev/redheadguy-guide-bot.git
cd redheadguy-guide-bot

# 2. Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Настройте .env
cp .env.example .env
nano .env

# 5. Запустите
python bot.py
```

---

## ⚙️ Переменные окружения (.env)

Скопируйте `.env.example` → `.env` и заполните нужные поля.

| Переменная | Обязат. | Описание |
|------------|:-------:|----------|
| `BOT_TOKEN` | ✅ | Токен бота от [@BotFather](https://t.me/BotFather). |
| `ADMIN_ID` | ✅ | Telegram ID администратора(ов), которым доступна админ-панель. Несколько ID — через запятую: `123456789,987654321` |
| `MAIN_BOT_URL` | ❌ | Ссылка на основной бот (для кнопки в гайдах). По умолчанию `https://t.me/your_main_bot` |
| `CHANNEL_URL` | ❌ | Ссылка на канал новостей (кнопка «📢 Канал новостей») |
| `CABINET_URL` | ❌ | Ссылка на личный кабинет (кнопка «👤 Личный кабинет») |
| `SUPPORT_URL` | ❌ | Ссылка на поддержку (кнопка «💬 Поддержка») |
| `SITE_URL` | ❌ | Ссылка на официальный сайт (кнопка «🌐 Сайт») |
| `BOT_USERNAME` | ✅* | Имя пользователя бота (без `@`) — для кнопки «Войти через Telegram» в веб-редакторе. Нужно для работы веб-панели. |
| `WEB_SITE_NAME` | ❌ | Название сайта в шапке веб-редактора. По умолчанию `RedheadGuy Admin`. |

> Дополнительные ссылки (`CHANNEL_URL`, `CABINET_URL` и т.д.) показываются как кнопки в конце
> гайда, если гайд при создании помечен опцией «показывать ссылки». Если переменная пустая —
> соответствующая кнопка не выводится.

Пример `.env`:

```env
# Обязательно
BOT_TOKEN=123456789:AAEjklmnopqrstuvwxyz_abcdefghijk

# Кому доступна админ-панель (ваш Telegram ID)
ADMIN_ID=123456789

# Ссылки RedheadGuy (кнопки в гайдах) — примеры
MAIN_BOT_URL=https://t.me/your_main_bot
CHANNEL_URL=https://t.me/your_channel
CABINET_URL=https://cabinet.example.com
SUPPORT_URL=https://t.me/your_support
SITE_URL=https://example.com

# Веб-редактор (FastAPI)
BOT_USERNAME=your_bot_username   # без @
# WEB_SITE_NAME=RedheadGuy Admin
```

---

## 🎛️ Админ-панель

Напишите боту команду:

```
/admin
```

Доступна **только** пользователям, указанным в `ADMIN_ID`. Позволяет:

- ➕ Добавлять категории и гайды (интерактивный мастер-диалог)
- ✏️ Редактировать существующие гайды (заголовок, текст, ссылка)
- 🗑️ Удалять гайды и категории
- 📂 Смотреть текущий контент
- 📦 Экспорт/импорт контента (бэкап в файл, восстановление, перенос между ботами)
- 📊 Статистика (пользователи, запуски, просмотры категорий и гайдов)
- 🔔 Автоматические уведомления о новых пользователях

---

## 🌐 Веб-редактор (FastAPI)

Полноценная панель управления гайдами через браузер. Работает в отдельном
контейнере вместе с ботом и использует тот же файл `data/guides.json`.

**Возможности:**
- 🔑 вход через **Telegram Login Widget** (доступ только для `ADMIN_ID`)
- 📂 создание / переименование / удаление категорий
- ✍️ **rich text редактор (TinyMCE)** для текста гайда
- 👁️ живое **превью** гайда при редактировании
- 🖱️ **drag-and-drop** сортировка категорий и гайдов
- 🔗 настройка ссылки, подписи кнопки и `show_bot_links`
- 📊 счётчики (категорий, гайдов, пользователей)

### Настройка доступа

1. В [@BotFather](https://t.me/BotFather) → Bot Settings → **Domain**
   укажите адрес, по которому доступен веб-редактор (например `redheadguide.redheadguy.ru`).
2. В `.env` укажите `BOT_USERNAME` (имя бота без `@`) и ваш `ADMIN_ID`.
3. Веб-редактор запускается автоматически при `docker compose up`.

### Деплой за обратным прокси (Nginx + HTTPS)

Рекомендуется повесить на домен через Nginx с TLS:

```nginx
server {
    server_name redheadguide.redheadguy.ru;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

> Порт `8000` в `docker-compose.yml` при необходимости можно поменять или
> убрать публикацию наружу, оставив доступ только через Nginx.

### Запуск веба без Docker

```bash
pip install -r web/requirements.txt
python -m uvicorn web.main:app --host 0.0.0.0 --port 8000
```

---

## 📊 Аналитика

Действия пользователей пишутся в файл `logs/analytics.log`:

```
2026-08-20 18:23:57 | START    | user_id=123456789 | username=example_user
2026-08-20 18:23:58 | CATEGORY | user_id=123456789 | category=happ | title=Happ
2026-08-20 18:23:59 | GUIDE    | user_id=123456789 | category=happ | guide_idx=0 | title=...
```

События: `START` (запуск бота), `CATEGORY` (просмотр категории), `GUIDE` (просмотр гайда).

Смотреть в реальном времени:

```bash
tail -f logs/analytics.log
```

---

## 🗂️ Структура проекта

```
redheadguy-guide-bot/
├── bot.py               # главный файл (логика бота)
├── admin.py             # админ-панель (CRUD контента)
├── config.py            # настройки / токен / ссылки / версия
├── guides.py            # доступ к контенту (загрузка/сохранение JSON)
├── keyboards.py         # клавиатуры (меню, категории, гайды)
├── states.py            # состояния мастер-диалогов (FSM)
├── users.py             # учёт пользователей (для уведомлений и статистики)
├── logger.py            # настройка логирования (консоль + файлы)
├── data/guides.json     # контент гайдов
├── media/photos/        # загруженные картинки-инструкции
├── logs/                # файлы логов и аналитики
├── web/                 # 🌐 веб-редактор (FastAPI)
│   ├── main.py          # FastAPI приложение (роуты)
│   ├── auth.py          # проверка подписи Telegram Login Widget
│   ├── config.py        # настройки веба
│   ├── storage.py       # работа с data/guides.json
│   ├── templates/       # Jinja2 шаблоны
│   ├── static/          # CSS + JS (TinyMCE, Sortable)
│   └── requirements.txt # зависимости веба
├── VERSION              # номер версии бота
├── CHANGELOG.md         # история версий
├── Dockerfile           # сборка образа бота
├── Dockerfile.web       # сборка образа веб-редактора
├── docker-compose.yml   # оркестрация (бот + web)
├── requirements.txt     # зависимости бота
├── .env.example         # шаблон настроек
└── README.md
```

---

## 🏷️ Changelog

Полный журнал версий — в [CHANGELOG.md](CHANGELOG.md).

### v1.3.1 (2026-08-20)
- 🔧 Исправлен вход в веб-редактор через Telegram
- 🔧 Гайды из TinyMCE корректно показываются в боте
- 🐳 Исправлен Docker-маунт `data/` для бота

### v1.3.0 (2026-08-20)
- 🌐 Веб-редактор на FastAPI (вход через Telegram, TinyMCE, drag-and-drop, превью)

### v1.2.0 (2026-08-20)
- 🔍 Поиск по гайдам (по названию и тексту)

### v1.1.0 (2026-08-20)
- 📦 Экспорт/импорт контента (бэкапы, перенос между ботами)
- 📊 Dashboard статистики в админке
- 🔔 Уведомления админу о новых пользователях

### v1.0.0 (2026-08-20) — первый релиз
- 🚀 Запуск бота на aiogram 3
- 🔐 Админ-панель: добавление, редактирование, удаление гайдов и категорий
- 📂 Хранение контента в JSON
- 📊 Аналитика действий пользователей
- 📝 Логирование (консоль + файл + аналитика)
- 🛡️ Обработка ошибок и защита от двойных нажатий
- 🖼️ Поддержка картинок-инструкций
- 🏷️ Команды `/version`, `/about`
- 🐳 Деплой через Docker Compose

---

## 📄 Лицензия

Проект распространяется «как есть» для личного использования RedheadGuy.
