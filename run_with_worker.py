#!/usr/bin/env python
"""
Скрипт для запуска Django сервера с автоматическим запуском воркера фоновых задач.
"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Добавляем корневую директорию проекта в Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Устанавливаем переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_tracker.settings')

import django
django.setup()

def run_server_and_worker():
    """Запускает Django сервер и воркер фоновых задач параллельно."""

    print("🚀 Запуск Django сервера с воркером фоновых задач...")
    print("=" * 60)

    # Команды для запуска
    server_cmd = [sys.executable, 'manage.py', 'runserver']
    worker_cmd = [sys.executable, 'manage.py', 'process_tasks', '--dev']

    # Запускаем воркер в фоне
    print("📋 Запуск воркера фоновых задач...")
    worker_process = subprocess.Popen(
        worker_cmd,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Даем воркеру время на запуск
    time.sleep(2)

    # Проверяем, что воркер запустился
    if worker_process.poll() is None:
        print("✅ Воркер фоновых задач запущен")
    else:
        print("❌ Ошибка запуска воркера")
        stdout, stderr = worker_process.communicate()
        print("stdout:", stdout)
        print("stderr:", stderr)
        return

    # Запускаем сервер
    print("🌐 Запуск Django сервера...")
    print("=" * 60)

    def signal_handler(signum, frame):
        """Обработчик сигналов для корректного завершения процессов."""
        print("\n🛑 Завершение процессов...")
        worker_process.terminate()
        worker_process.wait()
        print("✅ Все процессы завершены")
        sys.exit(0)

    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Запускаем сервер (блокирующий вызов)
        server_process = subprocess.run(server_cmd, cwd=BASE_DIR)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    finally:
        # Гарантируем завершение воркера
        if worker_process.poll() is None:
            worker_process.terminate()
            worker_process.wait()

if __name__ == '__main__':
    run_server_and_worker()