import os
import requests
from pathlib import Path
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
from .logger import logger
from .http_client import requests_get


def download_tmdb_poster(movie, size='w300', force=False):
    """
    Download and cache poster from TMDB
    
    Args:
        movie: Movie instance
        size: TMDB image size (w200, w300, w500, etc.)
        force: Force download even if already cached
    
    Returns:
        bool: Success status
    """
    if not force and not movie.needs_poster_refresh():
        logger.debug(f"Poster cache still valid for {movie.title}")
        return True
    
    if not movie.data or not movie.data.get('poster_path'):
        logger.warning(f"No poster path in TMDB data for {movie.title}")
        return False
    
    poster_path = movie.data['poster_path']
    poster_url = f"https://image.tmdb.org/t/p/{size}{poster_path}"
    
    try:
        logger.info(f"Downloading poster for {movie.title} from {poster_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.themoviedb.org/',
        }
        
        response = requests_get(poster_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        filename = f"tmdb_{movie.tmdb_id}_{size}.jpg"
        
        movie.poster_file.save(
            filename,
            ContentFile(response.content),
            save=False
        )
        movie.poster_cached_at = timezone.now()
        movie.save(update_fields=['poster_file', 'poster_cached_at'])
        
        logger.info(f"Successfully cached poster for {movie.title}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Failed to download poster for {movie.title}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error caching poster for {movie.title}: {e}")
        return False


def cleanup_orphaned_posters():
    """Remove poster files that are no longer referenced"""
    from .models import Movie
    
    media_root = Path(settings.MEDIA_ROOT) / 'posters'
    if not media_root.exists():
        return 0
    
    db_posters = set(
        Movie.objects.exclude(poster_file='')
        .exclude(poster_file__isnull=True)
        .values_list('poster_file', flat=True)
    )
    db_filenames = {Path(p).name for p in db_posters if p}
    
    removed = 0
    for poster_file in media_root.glob('tmdb_*.jpg'):
        if poster_file.name not in db_filenames:
            logger.info(f"Removing orphaned poster: {poster_file.name}")
            poster_file.unlink()
            removed += 1
    
    return removed
