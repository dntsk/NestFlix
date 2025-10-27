# AGENTS.md - NestFlix Codebase Guide

## Build/Test Commands
- `make server` - Run Django development server
- `make worker` - Run background task worker
- `make migrate` - Apply database migrations
- `python manage.py test` - Run all tests
- `python manage.py test catalog.tests` - Run catalog app tests
- `python manage.py test catalog.tests.ClassName` - Run specific test class
- `python manage.py test catalog.tests.ClassName.test_method` - Run single test

## Code Style Rules
- **Imports**: Standard Django imports first, then third-party, then local apps
- **Formatting**: 4-space indentation, maximum line length 79 characters
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Use try/except with specific exceptions
- **Models**: Use verbose_name and help_text for fields
- **Views**: Use @login_required decorator for views requiring authorization
- **Templates**: Use Django template language with proper inheritance
- **Type Hints**: Currently not used, follow existing patterns

## Testing
- Write tests in catalog/tests.py following Django TestCase patterns
- Use meaningful test method names starting with "test_"
- Test both success scenarios and error cases
- Mock external API calls in tests

## Logging
- **Library**: loguru (instead of print)
- **Configuration**: catalog/logger.py
- **Log Files**:
  - logs/nestflix.log (DEBUG level, 10 MB rotation, 30 days retention)
  - logs/errors.log (ERROR level, 10 MB rotation, 60 days retention)
- **Import**: `from .logger import logger, mask_sensitive`
- **Usage**:
  ```python
  logger.info("Information message")
  logger.debug("Debug information")
  logger.error("Error message")
  logger.warning("Warning")
  
  # Masking sensitive data
  logger.info(f"API key: {mask_sensitive(api_key)}")
  ```

## Plex Webhook Integration
- **Endpoint**: `/webhook/plex/<token>/` (CSRF exempt)
- **Token Generation**: `/settings/generate-plex-webhook/` (POST)
- **Disable**: `/settings/disable-plex-webhook/` (POST)
- **Models**:
  - `UserSettings`: fields `plex_webhook_token`, `plex_webhook_enabled`, `plex_webhook_created_at`
  - `PlexWebhookEvent`: logs all webhook events for audit
- **Processing**: `catalog/plex_utils.py`
  - `extract_tmdb_id_from_plex_guid(guid, guid_list=None)` - parse TMDB ID from Plex GUID or Guid array
  - `process_plex_event(user, event, payload)` - handle events (media.play, media.scrobble)
  - `log_webhook_event()` - save events to DB
- **Supported Events**:
  - `media.play`: Add content to collection (without watched status)
  - `media.scrobble`: Mark as watched and update watched_at date
  - **Important**: Every scrobble event updates watched_at, so rewatching moves content to top of library
  - **Language**: TMDB metadata fetched in user's preferred language from UserSettings.language
- **Supported Media Types**:
  - Movies: GUID formats `tmdb://`, `com.plexapp.agents.themoviedb://`
  - TV Shows: Extract TMDB ID from show (grandparent) GUID or episode Guid array
  - Episodes: Automatically detect parent show and track as TV series
- **GUID Formats**:
  - Direct: `tmdb://12345`, `com.plexapp.agents.themoviedb://12345?lang=en`
  - Plex native: `plex://movie/...`, `plex://episode/...` (requires Guid array with TMDB ID)
  - **Validation**: IDs > 10,000,000 are rejected (likely TVDB IDs)
  - **Filtering**: Only TMDB IDs extracted, TVDB/IMDB/etc ignored
- **Security**:
  - Unique UUID token for each user
  - All requests logged
  - Can be disabled/regenerated
  - Token masking in logs

## Poster Caching System
- **Storage**: Local filesystem in `media/posters/`
- **Models**: `Movie.poster_file` (ImageField), `Movie.poster_cached_at` (DateTimeField)
- **Methods**:
  - `Movie.get_poster_url()` - Get poster URL with fallback logic
  - `Movie.needs_poster_refresh()` - Check if poster needs re-caching (30 days default)
- **Template Tags**: `catalog/templatetags/poster_tags.py`
  - `{% poster_url movie %}` - Returns poster URL string
  - `{% movie_poster movie size='w300' css_class='...' %}` - Renders complete poster HTML with fallback
- **Fallback Logic**: Local cache → TMDB CDN → Placeholder
- **Background Tasks**: `catalog/tasks.py`
  - `cache_poster_task(movie_id)` - Cache single poster
  - `bulk_cache_posters_task(batch_size=10)` - Bulk cache operation
- **Management Commands**:
  - `python manage.py cache_posters [--all] [--limit N] [--force]` - Cache posters from TMDB
  - `python manage.py cleanup_posters` - Remove orphaned poster files
  - `python manage.py poster_stats` - Show cache statistics
- **Auto-caching**: Posters automatically cached when:
  - Movie added via UI (`catalog/views.py:add_movie`)
  - Movie added/updated via Plex webhook (`catalog/plex_utils.py:process_plex_event`)
- **Configuration**: `nestflix/settings.py`
  - `POSTER_CACHE_DAYS = 30` - Days before re-download
  - `POSTER_CACHE_SIZE = 'w300'` - TMDB image size
  - `MEDIA_ROOT` - Base path for media files
  - `MEDIA_URL` - URL prefix for media files
- **File Format**: `tmdb_{tmdb_id}_w300.jpg`

## Proxy Configuration
- **Support**: SOCKS5, HTTP, HTTPS proxies
- **Configuration**: Environment variables in `.env` or `settings.py`
- **Module**: `catalog/http_client.py` - centralized proxy handling
- **Variables**:
  - `PROXY_ENABLED` - Enable/disable proxy (True/False)
  - `SOCKS_PROXY` - SOCKS5 proxy URL (e.g., `socks5://127.0.0.1:1080`)
  - `HTTP_PROXY` - HTTP proxy URL
  - `HTTPS_PROXY` - HTTPS proxy URL
- **Authentication**: Supported via URL format `protocol://user:pass@host:port`
- **Logging**: Proxy usage logged at DEBUG level
- **Affected Components**:
  - TMDB API requests (movie data, search)
  - Trakt API requests (import data)
  - Poster downloads from TMDB CDN
- **Docker**: Use `host.docker.internal` to access host's proxy from container
- **Testing**:
  ```bash
  # Enable proxy
  export PROXY_ENABLED=True
  export SOCKS_PROXY=socks5://127.0.0.1:1080
  
  # Test
  python manage.py cache_posters --limit 1
  
  # Check logs
  tail -f logs/nestflix.log | grep proxy
  ```

## Secure Code Rules
- **Sensitive Data Protection**: API keys and Client IDs must be masked in logs (first 4 and last 4 characters)
- **Logging**: 
  - Use loguru for all messages
  - Never log full API keys, passwords, or tokens
  - Use mask_sensitive() function from catalog.logger for masking
  - Levels: DEBUG for debugging, INFO for information, ERROR for errors
- **Admin Panel**: Display only masked versions of sensitive data in admin interface
- **Validation**: Check API key length and format (TMDB: 32 characters, Trakt: 64 characters)
- **CSRF Protection**: All forms must contain {% csrf_token %}
- **Rate Limiting**: Limit request frequency to prevent abuse
- **Error Handling**: Do not expose internal error details in API responses
- **Data Storage**: Sensitive data must be stored encrypted in database
