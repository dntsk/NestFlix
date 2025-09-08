#!/bin/bash

# Скрипт для запуска Django сервера с воркером фоновых задач
echo "🚀 Запуск Movie Tracker с воркером..."
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
python manage.py runserver

# При завершении сервера завершаем воркер
cleanup