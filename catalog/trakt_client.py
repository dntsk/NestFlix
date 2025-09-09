import requests
from django.conf import settings

TRAKT_BASE_URL = 'https://api.trakt.tv'

def get_watched_movies(username: str, client_id: str) -> list[dict]:
    """Get watched movies from Trakt.tv."""
    try:
        print(f"DEBUG: Requesting watched movies for {username}")
        url = f"{TRAKT_BASE_URL}/users/{username}/watched/movies"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        print(f"DEBUG: URL: {url}")
        print(f"DEBUG: Headers: trakt-api-key={client_id[:4]}...{client_id[-4:]}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"DEBUG: Response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: Received {len(data)} watched movies")
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
        print(f"Error getting Trakt watched movies: {e}")
        return []

def get_watched_shows(username: str, client_id: str) -> list[dict]:
    """Get watched TV shows from Trakt.tv."""
    try:
        print(f"DEBUG: Requesting watched shows for {username}")
        url = f"{TRAKT_BASE_URL}/users/{username}/watched/shows"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        response = requests.get(url, headers=headers, timeout=30)
        print(f"DEBUG: Response status for shows: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: Received {len(data)} watched shows")
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
        print(f"Error getting Trakt watched shows: {e}")
        return []

def get_rated_movies(username: str, client_id: str) -> list[dict]:
    """Get rated movies from Trakt.tv."""
    try:
        print(f"DEBUG: Requesting rated movies for {username}")
        url = f"{TRAKT_BASE_URL}/users/{username}/ratings/movies"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        response = requests.get(url, headers=headers, timeout=30)
        print(f"DEBUG: Response status for rated movies: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: Received {len(data)} rated movies")
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
            print(f"DEBUG Trakt: Rated movie - {result['title']}, rating: {result['rating']}, tmdb_id: {result['tmdb_id']}")
            results.append(result)
        return results
    except requests.RequestException as e:
        print(f"Error getting Trakt rated movies: {e}")
        return []

def get_rated_shows(username: str, client_id: str) -> list[dict]:
    """Get rated TV shows from Trakt.tv."""
    try:
        print(f"DEBUG: Requesting rated shows for {username}")
        url = f"{TRAKT_BASE_URL}/users/{username}/ratings/shows"
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': client_id,
        }
        response = requests.get(url, headers=headers, timeout=30)
        print(f"DEBUG: Response status for rated shows: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: Received {len(data)} rated shows")
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
            print(f"DEBUG Trakt: Rated show - {result['title']}, rating: {result['rating']}, tmdb_id: {result['tmdb_id']}")
            results.append(result)
        return results
    except requests.RequestException as e:
        print(f"Error getting Trakt rated shows: {e}")
        return []