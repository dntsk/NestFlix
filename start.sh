#!/bin/bash

# Скрипт для запуска Django сервера с воркером фоновых задач
echo "🚀 Запуск NestFlix..."
echo "========================================"

# Функция для корректного завершения
cleanup() {
    echo ""
    echo "🛑 Завершение процессов..."
    kill 0
    exit 0
}

# Регистрируем обработчик сигнала
trap cleanup SIGINT SIGTERM

# Применяем миграции
echo "📦 Применение миграций базы данных..."
python manage.py migrate --noinput

if [ $? -ne 0 ]; then
    echo "❌ Ошибка применения миграций"
    exit 1
fi

echo "✅ Миграции применены"

# Собираем статику
echo "📦 Сборка статических файлов..."
python manage.py collectstatic --noinput

if [ $? -ne 0 ]; then
    echo "❌ Ошибка сборки статики"
    exit 1
fi

echo "✅ Статика собрана"

# Запускаем воркер в фоне
echo "📋 Запуск воркера фоновых задач..."
python manage.py process_tasks --dev &
WORKER_PID=$!

# Ждем немного, чтобы воркер запустился
sleep 2

# Проверяем, что воркер работает
if kill -0 $WORKER_PID 2>/dev/null; then
    echo "✅ Воркер запущен (PID: $WORKER_PID)"
else
    echo "❌ Ошибка запуска воркера"
    exit 1
fi

# Запускаем сервер
echo "🌐 Запуск Django сервера..."
echo "========================================"
gunicorn nestflix.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120

# При завершении сервера завершаем воркер
cleanup