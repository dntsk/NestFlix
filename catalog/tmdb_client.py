import requests
from django.conf import settings
from .logger import logger, mask_sensitive

TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def search_movies(query: str, api_key: str) -> list[dict]:
    """Search for movies and TV shows using TMDB API."""
    results = []
    logger.debug(f"Searching TMDB for query: '{query}'")
    
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            'api_key': api_key,
            'query': query,
            'language': 'ru-RU',
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        movie_count = len(data.get('results', []))
        logger.info(f"Found {movie_count} movies for query '{query}'")
        
        for item in data.get('results', []):
            results.append({
                'id': item['id'],
                'media_type': 'movie',
                'title': item.get('title', item.get('original_title', '')),
                'release_date': item.get('release_date', ''),
                'overview': item.get('overview', ''),
                'poster_path': item.get('poster_path', ''),
            })
    except requests.RequestException as e:
        logger.error(f"Error searching movies: {e}")

    try:
        url = f"{TMDB_BASE_URL}/search/tv"
        params = {
            'api_key': api_key,
            'query': query,
            'language': 'ru-RU',
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        tv_count = len(data.get('results', []))
        logger.info(f"Found {tv_count} TV shows for query '{query}'")
        
        for item in data.get('results', []):
            results.append({
                'id': item['id'],
                'media_type': 'tv',
                'title': item.get('name', item.get('original_name', '')),
                'release_date': item.get('first_air_date', ''),
                'overview': item.get('overview', ''),
                'poster_path': item.get('poster_path', ''),
            })
    except requests.RequestException as e:
        logger.error(f"Error searching TV shows: {e}")

    logger.debug(f"Total results for '{query}': {len(results)}")
    return results

def get_movie_details(media_type: str, tmdb_id: int, api_key: str) -> dict:
    """Get detailed movie/TV information from TMDB API."""
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}"
        params = {
            'api_key': api_key,
            'language': 'ru-RU',
        }
        logger.debug(f"Fetching TMDB details: {media_type}/{tmdb_id}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        data['media_type'] = media_type

        if media_type == 'movie':
            title_ru = data.get('title')
            title_orig = data.get('original_title')
            logger.debug(f"TMDB movie {tmdb_id}: ru='{title_ru}', orig='{title_orig}'")
            data['title'] = title_ru or title_orig or 'Unknown'
        else:
            name_ru = data.get('name')
            name_orig = data.get('original_name')
            logger.debug(f"TMDB show {tmdb_id}: ru='{name_ru}', orig='{name_orig}'")
            data['name'] = name_ru or name_orig or 'Unknown'

        logger.info(f"Successfully fetched TMDB details for {media_type}/{tmdb_id}")
        return data
    except requests.RequestException as e:
        logger.error(f"Error getting {media_type} details for {tmdb_id}: {e}")
        return {}