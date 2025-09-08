import requests
from django.conf import settings

TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def search_movies(query: str, api_key: str) -> list[dict]:
    """Search for movies and TV shows using TMDB API."""
    results = []
    try:
        # Search movies
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            'api_key': api_key,
            'query': query,
            'language': 'ru-RU',
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
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
        print(f"Error searching movies: {e}")

    try:
        # Search TV shows
        url = f"{TMDB_BASE_URL}/search/tv"
        params = {
            'api_key': api_key,
            'query': query,
            'language': 'ru-RU',
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for item in data.get('results', []):
            results.append({
                'id': item['id'],
                'media_type': 'tv',
                'title': item.get('name', item.get('original_name', '')),  # TV shows use 'name'
                'release_date': item.get('first_air_date', ''),
                'overview': item.get('overview', ''),
                'poster_path': item.get('poster_path', ''),
            })
    except requests.RequestException as e:
        print(f"Error searching TV shows: {e}")

    return results

def get_movie_details(media_type: str, tmdb_id: int, api_key: str) -> dict:
    """Get detailed movie/TV information from TMDB API."""
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}"
        params = {
            'api_key': api_key,
            'language': 'ru-RU',  # Russian for details
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        data['media_type'] = media_type  # Add media_type to data

        # Debug language info
        print(f"DEBUG TMDB: {media_type}/{tmdb_id}")
        if media_type == 'movie':
            title_ru = data.get('title')
            title_orig = data.get('original_title')
            print(f"DEBUG TMDB: Russian title: '{title_ru}', Original title: '{title_orig}'")
            data['title'] = title_ru or title_orig or 'Unknown'
        else:
            name_ru = data.get('name')
            name_orig = data.get('original_name')
            print(f"DEBUG TMDB: Russian name: '{name_ru}', Original name: '{name_orig}'")
            data['name'] = name_ru or name_orig or 'Unknown'

        return data
    except requests.RequestException as e:
        print(f"Error getting {media_type} details: {e}")
        return {}