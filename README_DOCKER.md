# NestFlix Docker Setup

## Quick Start

### 1. Build and run with Docker Compose

```bash
docker-compose up -d
```

### 2. Access the application

Open your browser and navigate to: http://localhost:8000

### 3. Create superuser (first time only)

```bash
docker-compose exec web python manage.py createsuperuser
```

## Environment Variables

Create a `.env` file in the project root (optional):

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_COOKIE_SECURE=False
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

## Docker Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f web
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Run Django management commands
```bash
docker-compose exec web python manage.py <command>
```

Examples:
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Apply migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## Data Persistence

Data is persisted in:
- `./db` - SQLite database

Логи доступны через Docker:
```bash
docker-compose logs -f web
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in environment variables
2. Generate a strong `SECRET_KEY`
3. Set `CSRF_COOKIE_SECURE=True`
4. Configure `ALLOWED_HOSTS` with your domain
5. Configure `CSRF_TRUSTED_ORIGINS` with your domain (e.g., `https://yourdomain.com`)
6. Use a reverse proxy (nginx/traefik) with HTTPS

Example production `.env`:
```env
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_COOKIE_SECURE=True
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Troubleshooting

### Port 8000 already in use
```bash
# Stop the container using that port
docker-compose down

# Or change the port in docker-compose.yaml
ports:
  - "8001:8000"
```

### Database issues
```bash
# Remove database and start fresh
docker-compose down
rm -rf db/db.sqlite3
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### View container logs
```bash
docker-compose logs -f web
```
