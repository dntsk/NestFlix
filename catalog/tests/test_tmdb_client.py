from django.test import TestCase
from unittest.mock import patch, Mock
import requests
from ..tmdb_client import search_movies, get_movie_details

class TMDBClientTest(TestCase):
    @patch('catalog.tmdb_client.requests.get')
    def test_search_movies_success(self, mock_get):
        mock_response_movie = Mock()
        mock_response_movie.json.return_value = {
            'results': [
                {
                    'id': 123,
                    'title': 'Test Movie',
                    'original_title': 'Test Movie Original',
                    'release_date': '2023-01-01',
                    'overview': 'Test overview',
                    'poster_path': '/test.jpg'
                }
            ]
        }
        mock_response_movie.raise_for_status.return_value = None
        
        mock_response_tv = Mock()
        mock_response_tv.json.return_value = {'results': []}
        mock_response_tv.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response_movie, mock_response_tv]

        results = search_movies('test', 'fake_api_key')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 123)
        self.assertEqual(results[0]['title'], 'Test Movie')
        self.assertEqual(results[0]['media_type'], 'movie')

    @patch('catalog.tmdb_client.requests.get')
    def test_search_movies_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException('Network error')

        results = search_movies('test', 'fake_api_key')

        self.assertEqual(results, [])

    @patch('catalog.tmdb_client.requests.get')
    def test_search_movies_empty_results(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = search_movies('test', 'fake_api_key')

        self.assertEqual(results, [])

    @patch('catalog.tmdb_client.requests.get')
    def test_get_movie_details_movie_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'title': 'Test Movie RU',
            'original_title': 'Test Movie',
            'overview': 'Test overview',
            'release_date': '2023-01-01'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_movie_details('movie', 123, 'fake_api_key')

        self.assertEqual(result['title'], 'Test Movie RU')
        self.assertEqual(result['media_type'], 'movie')

    @patch('catalog.tmdb_client.requests.get')
    def test_get_movie_details_tv_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'name': 'Test Show RU',
            'original_name': 'Test Show',
            'overview': 'Test overview',
            'first_air_date': '2023-01-01'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_movie_details('tv', 456, 'fake_api_key')

        self.assertEqual(result['name'], 'Test Show RU')
        self.assertEqual(result['media_type'], 'tv')

    @patch('catalog.tmdb_client.requests.get')
    def test_get_movie_details_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException('Network error')

        result = get_movie_details('movie', 123, 'fake_api_key')

        self.assertEqual(result, {})

    @patch('catalog.tmdb_client.requests.get')
    def test_get_movie_details_missing_title_fallback(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'original_title': 'Test Movie Original',
            'overview': 'Test overview'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_movie_details('movie', 123, 'fake_api_key')

        self.assertEqual(result['title'], 'Test Movie Original')

    @patch('catalog.tmdb_client.requests.get')
    def test_get_movie_details_missing_name_fallback(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'original_name': 'Test Show Original',
            'overview': 'Test overview'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_movie_details('tv', 456, 'fake_api_key')

        self.assertEqual(result['name'], 'Test Show Original')