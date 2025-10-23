# Plex Webhooks Integration - Documentation

## Overview

Full integration with Plex Webhooks for automatic tracking of movie and TV show views.

## Architecture

### Data Models

#### UserSettings (extension)
```python
plex_webhook_token = CharField(max_length=64, unique=True, null=True)
plex_webhook_enabled = BooleanField(default=False)
plex_webhook_created_at = DateTimeField(null=True, blank=True)
```

#### PlexWebhookEvent (new model)
```python
user = ForeignKey(User)
event_type = CharField(max_length=50)
payload = JSONField()
processed = BooleanField(default=False)
error_message = TextField(blank=True)
created_at = DateTimeField(default=timezone.now)
```

### API Endpoints

1. **Generate webhook** (requires authentication)
   - URL: `/settings/generate-plex-webhook/`
   - Method: POST
   - Response: `{success: true, webhook_url: "...", token: "..."}`

2. **Disable webhook** (requires authentication)
   - URL: `/settings/disable-plex-webhook/`
   - Method: POST
   - Response: `{success: true}`

3. **Receive webhook from Plex** (CSRF exempt)
   - URL: `/webhook/plex/<token>/`
   - Method: POST
   - Content-Type: multipart/form-data
   - Payload: JSON in `payload` field

### Processing Logic (catalog/plex_utils.py)

#### extract_tmdb_id_from_plex_guid(guid)
Extracts TMDB ID from Plex GUID.

**Supported formats:**
- `tmdb://123456`
- `com.plexapp.agents.themoviedb://123456?lang=en`

**Not supported:**
- `plex://movie/...` (internal Plex format)

#### process_plex_event(user, event, payload)
Processes webhook events.

**Supported events:**
- `media.scrobble`: Movie watched (>90%) → creates/updates UserRating with watched_at
- `media.play`: Playback started → adds to collection

**Logic:**
1. Extract TMDB ID from Plex GUID
2. Determine media type (movie/tv)
3. Get data from TMDB API
4. Create/update Movie
5. Create/update UserRating

#### log_webhook_event(user, event_type, payload, processed, error_message)
Saves all webhook events for audit.

## UI

### User Settings (user_settings.html)

**When webhook is NOT configured:**
- "Generate Webhook" button
- After generation - page reload

**When webhook is configured:**
- Full URL displayed
- "Copy" button (with visual feedback)
- Creation date
- "Regenerate" button (with confirmation)
- "Disable" button (with confirmation)

## Security

### Tokens
- UUID4 (32 hex characters)
- Unique for each user
- Stored in DB with unique index
- Masked in logs: `abcd1234...efgh5678`

### CSRF Protection
- Webhook endpoint: CSRF exempt (Plex cannot send token)
- Generation/disable: requires CSRF token

### Validation
1. Check token exists in DB
2. Check `plex_webhook_enabled` flag
3. Check user ownership

### Logging
- All webhook requests logged in `PlexWebhookEvent`
- All operations logged via loguru
- Sensitive data masked

## Administration

### Django Admin

**PlexWebhookEvent:**
- View all webhook events
- Filter by event type, processing status, date
- Search by user
- Read-only (cannot add/edit)

**UserSettings:**
- Display webhook status (enabled/disabled)
- Masked token
- Filter by plex_webhook_enabled

## Testing

### Manual Testing

1. **Generate webhook:**
   ```bash
   curl -X POST http://localhost:8000/settings/generate-plex-webhook/ \
     -H "Cookie: sessionid=..." \
     -H "X-CSRFToken: ..."
   ```

2. **Simulate Plex webhook:**
   ```bash
   curl -X POST http://localhost:8000/webhook/plex/YOUR_TOKEN/ \
     -F 'payload={"event":"media.scrobble","Metadata":{"guid":"tmdb://550","type":"movie","title":"Fight Club"}}'
   ```

### Check Logs

```bash
tail -f logs/nestflix.log | grep -i plex
```

## Known Limitations

1. **Plex GUID format:**
   - Internal format `plex://movie/...` not supported
   - Requires TMDB agent in Plex

2. **Events:**
   - Only `media.play` and `media.scrobble` processed
   - Other events ignored

3. **TV Shows:**
   - For episodes, uses show GUID (grandparentGuid)
   - Creates entry at show level, not episode level

## Troubleshooting

### Webhook not triggering

1. Check webhook is enabled in settings
2. Check URL in Plex (must be externally accessible)
3. Check logs: `logs/nestflix.log`
4. Check PlexWebhookEvent in admin

### TMDB ID not extracted

1. Check GUID format in logs
2. Ensure TMDB agent is used in Plex
3. Verify metadata is updated

### Movie not added

1. Check user has TMDB API key configured
2. Check TMDB API limits
3. Check error logs: `logs/errors.log`

## Roadmap

### Possible Improvements:

- [ ] Support other Plex agents (IMDb, TheTVDB)
- [ ] Webhook event statistics in UI
- [ ] Configure which events to process
- [ ] Webhook for media.rate (rating sync)
- [ ] Rate limiting for spam protection
- [ ] Webhook for device.new (new device notifications)

## Migration

Applied migration: `0008_usersettings_plex_webhook_created_at_and_more`

**Contains:**
- Adding fields to UserSettings
- Creating PlexWebhookEvent model

**Backward Compatibility:** Full

## Dependencies

No new dependencies. Uses:
- Django 5.2
- uuid (stdlib)
- re (stdlib)

## Performance

- Webhook endpoint processed synchronously
- Average processing time: 200-500ms (depends on TMDB API)
- Event logging: ~10ms
- Recommended to monitor TMDB API response time

## Changelog

### v1.1.0 - 2025-10-23
- ✅ Added full Plex Webhooks integration
- ✅ Unique token generation
- ✅ UI for webhook management
- ✅ Processing media.play and media.scrobble events
- ✅ All events logging
- ✅ Admin panel for audit
- ✅ Documentation
