#!/bin/bash
export GIT_SSH_COMMAND="/usr/bin/ssh -i /root/.ssh/id_ed25519_vps -o StrictHostKeyChecking=no"

# Путь к проекту
PROJECT_DIR="/root/crm_project"
LOG_FILE="/root/crm_project/logs/deploy.log"

# Функция логирования
log() {
    echo "[$(/usr/bin/date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== Начало деплоя ==="

cd "$PROJECT_DIR" || {
    log "ОШИБКА: Не удалось перейти в $PROJECT_DIR"
    exit 1
}

# Активируем виртуальное окружение
source /root/crm_project/venv/bin/activate || {
    log "ОШИБКА: Не удалось активировать venv"
    exit 1
}

# Получаем последние изменения
log "Выполняю git pull..."
/usr/bin/git pull origin main >> "$LOG_FILE" 2>&1
GIT_RESULT=$?

if [ $GIT_RESULT -ne 0 ]; then
    log "ОШИБКА: git pull завершился с кодом $GIT_RESULT"
    exit 1
fi

# Проверяем, есть ли миграции
log "Проверяю миграции..."
/root/crm_project/venv/bin/python manage.py showmigrations --plan | /usr/bin/grep -q "\[ \]"
if [ $? -eq 0 ]; then
    log "Обнаружены новые миграции, применяю..."
    /root/crm_project/venv/bin/python manage.py migrate >> "$LOG_FILE" 2>&1
fi

# Собираем статику
log "Собираю статику..."
/root/crm_project/venv/bin/python manage.py collectstatic --noinput >> "$LOG_FILE" 2>&1

# Перезапускаем Gunicorn
log "Перезапускаю Gunicorn..."
/usr/bin/systemctl restart crm >> "$LOG_FILE" 2>&1

# Проверяем статус
sleep 2
if /usr/bin/systemctl is-active --quiet crm; then
    log "✅ Деплой успешно завершён"
else
    log "❌ ОШИБКА: Gunicorn не запустился после деплоя"
    /usr/bin/systemctl status crm >> "$LOG_FILE" 2>&1
    exit 1
fi

log "=== Конец деплоя ==="
