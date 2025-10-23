import requests
from django.conf import settings
from .logger import logger, mask_sensitive

TRAKT_BASE_URL = 'https://api.trakt.tv'

def get_watched_movies(username: str, client_id: str) -> list[dict]:
    """Get watched movies from Trakt.tv."""
    try:
        url = f"{TRAKT_BASE_URL}/users/{username}/watched/movies"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        logger.info(f"Requesting watched movies for user: {username}")
        logger.debug(f"Trakt API URL: {url}, client_id: {mask_sensitive(client_id)}")
        
        response = requests.get(url, headers=headers, timeout=30)
        logger.debug(f"Trakt API response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Received {len(data)} watched movies for {username}")
        
        results = []
        for item in data:
            movie = item['movie']
            results.append({
                'trakt_id': movie['ids']['trakt'],
                'tmdb_id': movie['ids'].get('tmdb'),
                'title': movie['title'],
                'year': movie.get('year'),
                'media_type': 'movie',
                'last_watched_at': item.get('last_watched_at'),
            })
        return results
    except requests.RequestException as e:
        logger.error(f"Error getting Trakt watched movies for {username}: {e}")
        return []

def get_watched_shows(username: str, client_id: str) -> list[dict]:
    """Get watched TV shows from Trakt.tv."""
    try:
        url = f"{TRAKT_BASE_URL}/users/{username}/watched/shows"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        logger.info(f"Requesting watched shows for user: {username}")
        
        response = requests.get(url, headers=headers, timeout=30)
        logger.debug(f"Trakt shows response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Received {len(data)} watched shows for {username}")
        
        results = []
        for item in data:
            show = item['show']
            results.append({
                'trakt_id': show['ids']['trakt'],
                'tmdb_id': show['ids'].get('tmdb'),
                'title': show['title'],
                'year': show.get('year'),
                'media_type': 'tv',
                'last_watched_at': item.get('last_watched_at'),
            })
        return results
    except requests.RequestException as e:
        logger.error(f"Error getting Trakt watched shows for {username}: {e}")
        return []

def get_rated_movies(username: str, client_id: str) -> list[dict]:
    """Get rated movies from Trakt.tv."""
    try:
        url = f"{TRAKT_BASE_URL}/users/{username}/ratings/movies"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        logger.info(f"Requesting rated movies for user: {username}")
        
        response = requests.get(url, headers=headers, timeout=30)
        logger.debug(f"Trakt rated movies response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Received {len(data)} rated movies for {username}")
        
        results = []
        for item in data:
            movie = item['movie']
            result = {
                'trakt_id': movie['ids']['trakt'],
                'tmdb_id': movie['ids'].get('tmdb'),
                'title': movie['title'],
                'rating': item['rating'],
                'rated_at': item.get('rated_at'),
                'media_type': 'movie',
            }
            logger.debug(f"Rated movie: {result['title']} (rating: {result['rating']}, tmdb_id: {result['tmdb_id']})")
            results.append(result)
        return results
    except requests.RequestException as e:
        logger.error(f"Error getting Trakt rated movies for {username}: {e}")
        return []

def get_rated_shows(username: str, client_id: str) -> list[dict]:
    """Get rated TV shows from Trakt.tv."""
    try:
        url = f"{TRAKT_BASE_URL}/users/{username}/ratings/shows"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        logger.info(f"Requesting rated shows for user: {username}")
        
        response = requests.get(url, headers=headers, timeout=30)
        logger.debug(f"Trakt rated shows response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Received {len(data)} rated shows for {username}")
        
        results = []
        for item in data:
            show = item['show']
            result = {
                'trakt_id': show['ids']['trakt'],
                'tmdb_id': show['ids'].get('tmdb'),
                'title': show['title'],
                'rating': item['rating'],
                'rated_at': item.get('rated_at'),
                'media_type': 'tv',
            }
            logger.debug(f"Rated show: {result['title']} (rating: {result['rating']}, tmdb_id: {result['tmdb_id']})")
            results.append(result)
        return results
    except requests.RequestException as e:
        logger.error(f"Error getting Trakt rated shows for {username}: {e}")
        return []