# Logging Guide

## Overview

The project uses **Loguru** library for structured and efficient logging.

## Configuration

Logging settings are located in `catalog/logger.py`:

- **Console Output**: INFO and above, with color highlighting
- **File Logging**:
  - `logs/nestflix.log` - all messages (DEBUG+)
  - `logs/errors.log` - errors only (ERROR+)
- **Rotation**: 10 MB with automatic ZIP archiving
- **Retention**: 30 days for main logs, 60 days for errors

## Usage

### Basic Import

```python
from .logger import logger, mask_sensitive
```

### Logging Examples

```python
# Information messages
logger.info("User successfully authenticated")

# Debug information
logger.debug(f"Received {count} records from API")

# Errors
logger.error(f"Failed to connect to API: {error}")

# Warnings
logger.warning("API key not configured")
```

### Masking Sensitive Data

```python
# Masking API keys and tokens
api_key = "1234567890abcdef1234567890abcdef"
logger.info(f"API key: {mask_sensitive(api_key)}")
# Output: API key: 1234...cdef

# Short values are fully hidden
short_value = "123"
logger.info(f"Value: {mask_sensitive(short_value)}")
# Output: Value: ***
```

## Logging Levels

| Level    | Usage |
|----------|-------|
| DEBUG    | Detailed debugging information for development |
| INFO     | Confirmation of normal application operation |
| WARNING  | Warnings about potential issues |
| ERROR    | Errors requiring attention |

## Security Rules

⚠️ **NEVER** log:
- Full API keys
- Passwords
- Authorization tokens
- User personal data

✅ **ALWAYS** use `mask_sensitive()` for:
- API keys (TMDB, Trakt)
- Client ID
- Any secret values

## Viewing Logs

```bash
# Latest entries from main log
tail -f logs/nestflix.log

# Errors only
tail -f logs/errors.log

# Search in logs
grep "import" logs/nestflix.log
```

## Integration in New Code

When adding new functionality:

1. Import logger at the beginning of file:
   ```python
   from .logger import logger, mask_sensitive
   ```

2. Replace all `print()` with appropriate logger calls:
   ```python
   # Before
   print(f"Starting task: {task_id}")
   
   # After
   logger.info(f"Starting task: {task_id}")
   ```

3. Mask sensitive data:
   ```python
   logger.debug(f"API key: {mask_sensitive(api_key)}")
   ```

## Production Monitoring

Recommended setup:
- Monitor `logs/` directory size
- Alerts for ERROR messages
- Regular log rotation (automatic)
- Log archive backups
