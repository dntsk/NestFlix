# NestFlix

NestFlix - is web application built with Django for tracking watched movies, managing personal collection and integrating with external services TMDB and Trakt.tv.

## Features

- **Personal Movie Library**: Add, rate and track watched movies
- **Public Library**: View popular movies by average user ratings
- **Movie Search**: TMDB API integration for searching and fetching movie information
- **Local Poster Caching**: Automatic local caching of movie posters with fallback support
- **Import from Trakt.tv**: Sync watched movies and ratings data
- **Plex Webhooks**: Automatic tracking of views from Plex Media Server (requires Plex Pass)
- **Settings Management**: Configure API keys for TMDB, Trakt and Plex webhooks
- **Responsive Design**: Adaptive interface using Pico CSS

## Technologies

- **Backend**: Django 5.2
- **Frontend**: HTML, CSS (Pico CSS), JavaScript (HTMX)
- **Database**: SQLite (by default)
- **Logging**: Loguru with rotation and archiving
- **External APIs**:
  - TMDB (The Movie Database)
  - Trakt.tv
- **Additional**: Background tasks for data import

## Installation

### Prerequisites

- Python 3.8+
- pip
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/nestflix.git
   cd nestflix
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create file `.env`:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your settings.

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

## Configuration

### API Keys

To use the application fully, you need to configure API keys:

1. **TMDB API Key**:
   - Register on [TMDB](https://www.themoviedb.org/)
   - Get your API key in account settings
   - In the application go to "Settings" and enter TMDB API Key

2. **Trakt.tv API**:
   - Register on [Trakt.tv](https://trakt.tv/)
   - Go to [Applications](https://trakt.tv/oauth/applications) and create a new application
   - Fill in the required fields (Name, Description, Redirect uri you can specify `urn:ietf:wg:oauth:2.0:oob`)
   - Получите **Client ID** (required) и **Client Secret** (optional)
   - In the application go to "Settings" and enter:
     - **Trakt.tv Username** - your username on Trakt.tv
     - **Trakt.tv Client ID** - Client ID of your application

### Environment Variables

Create file `.env` in project root:

```env
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Note**: API Keys для TMDB и Trakt.tv are configured via user interface in "Settings" and stored in database.

## Running

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run development server:**
   ```bash
   python manage.py runserver
   ```

3. **Open browser and go to:**
   ```
   http://localhost:8000
   ```

## Usage

### For New Users

1. Register or login
2. Configure TMDB API Key in Settings
3. Start searching and adding movies

### Main Features

- **Home Page**: View popular movies (for unauthorized users) or personal library (for authorized users)
- **Movie Search**: Use search bar to find movies
- **Adding a Movie**: Click on a movie in search results to add to collection
- **Rating Movies**: Rate and mark watched movies
- **Import from Trakt**: Sync data from Trakt.tv account

### Poster Caching Management

NestFlix automatically caches movie posters locally to improve performance and reliability:

**Automatic Caching:**
- Posters are cached automatically when movies are added via UI
- Plex webhook integration also triggers automatic poster caching
- Cached posters are refreshed every 30 days

**Manual Management Commands:**

```bash
# Cache missing posters (first 50)
python manage.py cache_posters --limit 50

# Force re-cache all posters
python manage.py cache_posters --all --force

# Show cache statistics
python manage.py poster_stats

# Remove orphaned poster files
python manage.py cleanup_posters
```

**Fallback System:**
1. Local cached poster (fastest)
2. TMDB CDN (if cache expired or missing)
3. Placeholder image (if poster unavailable)


## Project Structure

```
nestflix/
├── catalog/                 # Main application
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates
│   │   └── catalog/
│   ├── static/             # Static files
│   ├── models.py           # Data models
│   ├── views.py            # Views
│   ├── urls.py             # URL routes
│   ├── tmdb_client.py      # TMDB API client
│   ├── trakt_client.py     # Trakt API client
│   └── tasks.py            # Background tasks
├── nestflix/               # Project settings
│   ├── settings.py         # Main settings
│   ├── urls.py             # Root URLs
│   └── wsgi.py             # WSGI configuration
├── media/                  # Media files (uploaded by users)
├── staticfiles/            # Collected static files
├── db.sqlite3              # Database
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Data models

- **Movie**: Movie information (TMDB ID, data from API)
- **UserRating**: User ratings, watch status
- **UserSettings**: User settings (API Keys)
- **ImportTask**: Import tasks from Trakt.tv

## API интеграции

### TMDB API
- Movie Search
- Get detailed movie information
- Posters and images

### Trakt.tv API
- **Authentication type**: Client ID (without OAuth)
- **Data to import**:
  - Watched movies
  - Movie and TV show ratings
  - История просмотроin
- **Features**: Import via public API without full OAuth authentication

## Development

### Adding New Features

1. Create a new development branch
2. Implement the feature
3. Write tests
4. Create a pull request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments to complex code sections

## Deployment

### Production settings

1. Set `DEBUG=False` in settings.py
2. Configure static files:
   ```bash
   python manage.py collectstatic
   ```
3. Use production-ready web server (Gunicorn, uWSGI)
4. Configure базу данных (PostgreSQL recommended for production)

### Docker

**Quick Start:**

```bash
# Build and run with Docker Compose
docker-compose up -d

# Run migrations (first time only)
docker-compose exec web python manage.py migrate

# Create superuser (first time only)
docker-compose exec web python manage.py createsuperuser

# Cache posters (optional)
docker-compose exec web python manage.py cache_posters --limit 50
```

**Persistent Data:**

Docker Compose configuration includes volumes for:
- `./db` - SQLite database
- `./media` - Cached movie posters
- `./logs` - Application logs

All data persists between container restarts.

**Environment Variables:**

Create `.env` file or use environment variables in `docker-compose.yaml`:
```env
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```
