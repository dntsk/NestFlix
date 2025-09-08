# Makefile для Movie Tracker

.PHONY: help run run-python run-bash server worker migrate createsuperuser clean

help:
	@echo "Доступные команды:"
	@echo "  make run          - Запуск сервера с воркером (Python скрипт)"
	@echo "  make run-bash     - Запуск сервера с воркером (Bash скрипт)"
	@echo "  make server       - Только Django сервер"
	@echo "  make worker       - Только воркер фоновых задач"
	@echo "  make migrate      - Применить миграции"
	@echo "  make createsuperuser - Создать суперпользователя"
	@echo "  make clean        - Очистка Python кэша"

run:
	@echo "🚀 Запуск с Python скриптом..."
	python run_with_worker.py

run-bash:
	@echo "🚀 Запуск с Bash скриптом..."
	./start.sh

server:
	@echo "🌐 Запуск Django сервера..."
	python manage.py runserver

worker:
	@echo "📋 Запуск воркера фоновых задач..."
	python manage.py process_tasks --dev

migrate:
	@echo "📊 Применение миграций..."
	python manage.py migrate

createsuperuser:
	@echo "👤 Создание суперпользователя..."
	python manage.py createsuperuser

clean:
	@echo "🧹 Очистка кэша..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete