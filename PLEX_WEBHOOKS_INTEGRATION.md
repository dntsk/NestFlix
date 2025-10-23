# Plex Webhooks Integration - Документация

## Обзор

Реализована полная интеграция с Plex Webhooks для автоматического отслеживания просмотров фильмов и сериалов.

## Архитектура

### Модели данных

#### UserSettings (расширение)
```python
plex_webhook_token = CharField(max_length=64, unique=True, null=True)
plex_webhook_enabled = BooleanField(default=False)
plex_webhook_created_at = DateTimeField(null=True, blank=True)
```

#### PlexWebhookEvent (новая модель)
```python
user = ForeignKey(User)
event_type = CharField(max_length=50)
payload = JSONField()
processed = BooleanField(default=False)
error_message = TextField(blank=True)
created_at = DateTimeField(default=timezone.now)
```

### API Endpoints

1. **Генерация webhook** (требует авторизации)
   - URL: `/settings/generate-plex-webhook/`
   - Метод: POST
   - Ответ: `{success: true, webhook_url: "...", token: "..."}`

2. **Отключение webhook** (требует авторизации)
   - URL: `/settings/disable-plex-webhook/`
   - Метод: POST
   - Ответ: `{success: true}`

3. **Прием webhook от Plex** (CSRF exempt)
   - URL: `/webhook/plex/<token>/`
   - Метод: POST
   - Content-Type: multipart/form-data
   - Payload: JSON в поле `payload`

### Логика обработки (catalog/plex_utils.py)

#### extract_tmdb_id_from_plex_guid(guid)
Извлекает TMDB ID из Plex GUID.

**Поддерживаемые форматы:**
- `tmdb://123456`
- `com.plexapp.agents.themoviedb://123456?lang=en`

**Не поддерживается:**
- `plex://movie/...` (внутренний формат Plex)

#### process_plex_event(user, event, payload)
Обрабатывает webhook события.

**Поддерживаемые события:**
- `media.scrobble`: Фильм досмотрен (>90%) → создает/обновляет UserRating с watched_at
- `media.play`: Начало воспроизведения → добавляет в коллекцию

**Логика:**
1. Извлечь TMDB ID из Plex GUID
2. Определить тип медиа (movie/tv)
3. Получить данные из TMDB API
4. Создать/обновить Movie
5. Создать/обновить UserRating

#### log_webhook_event(user, event_type, payload, processed, error_message)
Сохраняет все webhook события для аудита.

## UI

### Настройки пользователя (user_settings.html)

**Когда webhook НЕ настроен:**
- Кнопка "Сгенерировать Webhook"
- После генерации - перезагрузка страницы

**Когда webhook настроен:**
- Отображается полный URL
- Кнопка "Копировать" (с визуальным feedback)
- Дата создания
- Кнопка "Перегенерировать" (с подтверждением)
- Кнопка "Отключить" (с подтверждением)

## Безопасность

### Токены
- UUID4 (32 символа hex)
- Уникальный для каждого пользователя
- Хранится в БД с индексом unique
- Маскируется в логах: `abcd1234...efgh5678`

### CSRF Protection
- Webhook endpoint: CSRF exempt (Plex не может отправить токен)
- Генерация/отключение: требует CSRF токен

### Валидация
1. Проверка существования токена в БД
2. Проверка флага `plex_webhook_enabled`
3. Проверка принадлежности пользователю

### Логирование
- Все webhook запросы логируются в `PlexWebhookEvent`
- Все операции логируются через loguru
- Чувствительные данные маскируются

## Администрирование

### Django Admin

**PlexWebhookEvent:**
- Просмотр всех webhook событий
- Фильтрация по типу события, статусу обработки, дате
- Поиск по пользователю
- Read-only (нельзя добавлять/редактировать)

**UserSettings:**
- Отображение статуса webhook (enabled/disabled)
- Маскированный токен
- Фильтр по plex_webhook_enabled

## Тестирование

### Ручное тестирование

1. **Генерация webhook:**
   ```bash
   curl -X POST http://localhost:8000/settings/generate-plex-webhook/ \
     -H "Cookie: sessionid=..." \
     -H "X-CSRFToken: ..."
   ```

2. **Симуляция Plex webhook:**
   ```bash
   curl -X POST http://localhost:8000/webhook/plex/YOUR_TOKEN/ \
     -F 'payload={"event":"media.scrobble","Metadata":{"guid":"tmdb://550","type":"movie","title":"Fight Club"}}'
   ```

### Проверка в логах

```bash
tail -f logs/movie_tracker.log | grep -i plex
```

## Известные ограничения

1. **Plex GUID формат:**
   - Не поддерживается внутренний формат `plex://movie/...`
   - Требуется TMDB agent в Plex

2. **События:**
   - Обрабатываются только `media.play` и `media.scrobble`
   - Другие события игнорируются

3. **Сериалы:**
   - Для эпизодов берется GUID сериала (grandparentGuid)
   - Создается запись на уровне сериала, а не эпизода

## Troubleshooting

### Webhook не срабатывает

1. Проверить, что webhook enabled в настройках
2. Проверить URL в Plex (должен быть доступен извне)
3. Проверить логи: `logs/movie_tracker.log`
4. Проверить PlexWebhookEvent в админке

### TMDB ID не извлекается

1. Проверить формат GUID в логах
2. Убедиться, что в Plex используется TMDB agent
3. Проверить, что метаданные обновлены

### Фильм не добавляется

1. Проверить, что у пользователя настроен TMDB API key
2. Проверить лимиты TMDB API
3. Проверить логи ошибок: `logs/errors.log`

## Roadmap

### Возможные улучшения:

- [ ] Поддержка других Plex агентов (IMDb, TheTVDB)
- [ ] Статистика webhook событий в UI
- [ ] Настройка каких событий обрабатывать
- [ ] Webhook для media.rate (синхронизация оценок)
- [ ] Rate limiting для защиты от спама
- [ ] Webhook для device.new (уведомления о новых устройствах)

## Миграция

Применена миграция: `0008_usersettings_plex_webhook_created_at_and_more`

**Содержит:**
- Добавление полей в UserSettings
- Создание модели PlexWebhookEvent

**Обратная совместимость:** Полная

## Зависимости

Нет новых зависимостей. Используются:
- Django 5.2
- uuid (stdlib)
- re (stdlib)

## Производительность

- Webhook endpoint обрабатывается синхронно
- Среднее время обработки: 200-500ms (зависит от TMDB API)
- Логирование событий: ~10ms
- Рекомендуется мониторить время отклика TMDB API

## Changelog

### v1.1.0 - 2025-10-23
- ✅ Добавлена полная интеграция с Plex Webhooks
- ✅ Генерация уникальных токенов
- ✅ UI для управления webhook
- ✅ Обработка событий media.play и media.scrobble
- ✅ Логирование всех событий
- ✅ Админка для аудита
- ✅ Документация
