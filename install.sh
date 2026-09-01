#!/usr/bin/env bash
# ==============================================================================
# RedheadGuy Guide Bot v2.0.0 — Interactive Installer & Management Script
# Supported OS: Ubuntu 22.04 / 24.04 LTS & Debian Linux
# ==============================================================================

set -e

COLOR_RED="\033[0;31m"
COLOR_GREEN="\033[0;32m"
COLOR_YELLOW="\033[0;33m"
COLOR_CYAN="\033[0;36m"
COLOR_RESET="\033[0m"

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
log_info() {
    echo -e "${COLOR_CYAN}[INFO]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Скрипт должен быть запущен с правами root или через sudo!"
        exit 1
    fi
}

check_dependencies() {
    log_info "Проверка системных зависимостей..."

    # Update packages and install prerequisites
    apt-get update -qq >/dev/null 2>&1 || true
    apt-get install -y -qq curl git jq tar ufw ca-certificates gnupg >/dev/null 2>&1 || true

    # Docker Installation
    if ! command -v docker &>/dev/null; then
        log_info "Docker не найден. Установка официального Docker Engine..."
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes >/dev/null 2>&1 || true
        chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update -qq >/dev/null 2>&1 || true
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null 2>&1 || true
        log_success "Docker успешно установлен!"
    fi

    # Docker Compose Plugin check
    if ! docker compose version &>/dev/null; then
        log_info "Установка docker-compose-plugin..."
        apt-get install -y -qq docker-compose-plugin >/dev/null 2>&1 || true
    fi
}

configure_env() {
    if [ ! -f ".env" ]; then
        log_warning "Файл настроек .env не найден. Запуск мастера первоначальной настройки..."
        echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"
        echo -e "${COLOR_CYAN}   Мастер конфигурации RedheadGuy Guide Bot v2.0    ${COLOR_RESET}"
        echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"

        read -rp "Введите BOT_TOKEN от @BotFather: " input_bot_token
        read -rp "Введите ваш Telegram ADMIN_ID (через запятую): " input_admin_id
        read -rp "Введите BOT_USERNAME (без @, напр. redheadguy_bot): " input_bot_username
        read -rp "Введите название сайта [RedheadGuy Admin]: " input_site_name
        input_site_name=${input_site_name:-RedheadGuy Admin}

        cp .env.example .env
        sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=${input_bot_token}|g" .env
        sed -i "s|ADMIN_ID=.*|ADMIN_ID=${input_admin_id}|g" .env
        sed -i "s|BOT_USERNAME=.*|BOT_USERNAME=${input_bot_username}|g" .env
        sed -i "s|WEB_SITE_NAME=.*|WEB_SITE_NAME=${input_site_name}|g" .env

        log_success "Файл .env успешно создан и заполнен!"
    else
        log_info "Файл .env уже существует."
    fi
}

create_backup() {
    log_info "Создание резервной копии данных..."
    BACKUP_DIR="${APP_DIR}/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"

    tar -czf "$BACKUP_FILE" data media 2>/dev/null || true
    log_success "Резервная копия сохранена в: ${BACKUP_FILE}"
}

# ------------------------------------------------------------------------------
# Menu Actions
# ------------------------------------------------------------------------------
action_install_launch() {
    check_root
    check_dependencies
    configure_env
    log_info "Запуск стека через Docker Compose..."
    docker compose up -d --build
    log_success "Стек RedheadGuy Guide Bot v2.0.0 успешно запущен!"
    echo -e "Веб-панель доступна по адресу: ${COLOR_CYAN}http://localhost:8000${COLOR_RESET}"
}

action_restart() {
    log_info "Перезапуск всех сервисов..."
    docker compose restart
    log_success "Все сервисы перезапущены!"
}

action_logs() {
    log_info "Просмотр логов в реальном времени (Ctrl+C для выхода)..."
    docker compose logs -f
}

action_update() {
    check_root
    create_backup
    log_info "Обновление исходного кода из GitHub..."
    git pull origin $(git rev-parse --abbrev-ref HEAD) || true
    log_info "Пересборка и перезапуск контейнеров..."
    docker compose up -d --build
    log_success "Проект успешно обновлен без потери данных!"
}

action_uninstall() {
    check_root
    echo -e "${COLOR_RED}====================================================${COLOR_RESET}"
    echo -e "${COLOR_RED}                ВНИМАНИЕ! УДАЛЕНИЕ                  ${COLOR_RESET}"
    echo -e "${COLOR_RED}====================================================${COLOR_RESET}"
    read -rp "Вы уверены, что хотите полностью удалить стек? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        create_backup
        log_info "Остановка и удаление контейнеров..."
        docker compose down -v --remove-orphans || true

        read -rp "Удалить ли локальную папку data/ с гайдами? (y/N): " purge_data
        if [[ "$purge_data" =~ ^[Yy]$ ]]; then
            rm -rf data media
            log_warning "Папки data/ и media/ удалены."
        else
            log_info "Папки с данными сохранены."
        fi
        log_success "Стек успешно удален!"
    else
        log_info "Отмена удаления."
    fi
}

# ------------------------------------------------------------------------------
# Main TUI Menu
# ------------------------------------------------------------------------------
show_menu() {
    clear
    echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"
    echo -e "${COLOR_CYAN}   🤖 RedheadGuy Guide Bot v2.0.0 — Панель         ${COLOR_RESET}"
    echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"
    echo -e " 1) ${COLOR_GREEN}[1] Установить / Запустить стек${COLOR_RESET}"
    echo -e " 2) ${COLOR_CYAN}[2] Перезапустить сервисы${COLOR_RESET}"
    echo -e " 3) ${COLOR_CYAN}[3] Логи в реальном времени${COLOR_RESET}"
    echo -e " 4) ${COLOR_YELLOW}[4] Создать резервную копию (data + media)${COLOR_RESET}"
    echo -e " 5) ${COLOR_CYAN}[5] Обновить проект из GitHub${COLOR_RESET}"
    echo -e " 6) ${COLOR_RED}[6] Полное удаление стека${COLOR_RESET}"
    echo -e " 0) [0] Выход"
    echo -e "${COLOR_CYAN}====================================================${COLOR_RESET}"
    read -rp "Выберите пункт меню [0-6]: " choice

    case $choice in
        1) action_install_launch ;;
        2) action_restart ;;
        3) action_logs ;;
        4) create_backup ;;
        5) action_update ;;
        6) action_uninstall ;;
        0) exit 0 ;;
        *) log_error "Неверный пункт меню!"; sleep 1 ;;
    esac
}

# Main Execution Flow
if [ "$#" -gt 0 ]; then
    case "$1" in
        install) action_install_launch ;;
        restart) action_restart ;;
        logs) action_logs ;;
        backup) create_backup ;;
        update) action_update ;;
        uninstall) action_uninstall ;;
        *) echo "Использование: $0 {install|restart|logs|backup|update|uninstall}" ;;
    esac
else
    while true; do
        show_menu
        read -rp "Нажмите Enter для продолжения..."
    done
fi
