from django.test import TestCase
from unittest.mock import patch, Mock
import requests
from ..trakt_client import get_watched_movies, get_watched_shows, get_rated_movies, get_rated_shows

class TraktClientTest(TestCase):
    @patch('catalog.trakt_client.requests.get')
    def test_get_watched_movies_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'movie': {
                    'title': 'Test Movie',
                    'year': 2023,
                    'ids': {'trakt': 1, 'tmdb': 123}
                },
                'last_watched_at': '2023-01-01T00:00:00Z'
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = get_watched_movies('test_user', 'fake_client_id')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Movie')
        self.assertEqual(results[0]['tmdb_id'], 123)
        self.assertEqual(results[0]['media_type'], 'movie')

    @patch('catalog.trakt_client.requests.get')
    def test_get_watched_movies_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException('Network error')

        results = get_watched_movies('test_user', 'fake_client_id')

        self.assertEqual(results, [])

    @patch('catalog.trakt_client.requests.get')
    def test_get_watched_movies_empty_results(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = get_watched_movies('test_user', 'fake_client_id')

        self.assertEqual(results, [])

    @patch('catalog.trakt_client.requests.get')
    def test_get_watched_shows_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'show': {
                    'title': 'Test Show',
                    'year': 2023,
                    'ids': {'trakt': 2, 'tmdb': 456}
                },
                'last_watched_at': '2023-01-01T00:00:00Z'
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = get_watched_shows('test_user', 'fake_client_id')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Show')
        self.assertEqual(results[0]['tmdb_id'], 456)
        self.assertEqual(results[0]['media_type'], 'tv')

    @patch('catalog.trakt_client.requests.get')
    def test_get_rated_movies_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'movie': {
                    'title': 'Test Movie',
                    'year': 2023,
                    'ids': {'trakt': 1, 'tmdb': 123}
                },
                'rating': 8,
                'rated_at': '2023-01-01T00:00:00Z'
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = get_rated_movies('test_user', 'fake_client_id')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Movie')
        self.assertEqual(results[0]['rating'], 8)
        self.assertEqual(results[0]['tmdb_id'], 123)

    @patch('catalog.trakt_client.requests.get')
    def test_get_rated_shows_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'show': {
                    'title': 'Test Show',
                    'year': 2023,
                    'ids': {'trakt': 2, 'tmdb': 456}
                },
                'rating': 9,
                'rated_at': '2023-01-01T00:00:00Z'
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = get_rated_shows('test_user', 'fake_client_id')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Show')
        self.assertEqual(results[0]['rating'], 9)
        self.assertEqual(results[0]['tmdb_id'], 456)

    @patch('catalog.trakt_client.requests.get')
    def test_get_watched_movies_missing_tmdb_id(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'movie': {
                    'title': 'Test Movie',
                    'year': 2023,
                    'ids': {'trakt': 1}  # No tmdb_id
                },
                'last_watched_at': '2023-01-01T00:00:00Z'
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = get_watched_movies('test_user', 'fake_client_id')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Movie')
        self.assertIsNone(results[0]['tmdb_id'])

    @patch('catalog.trakt_client.requests.get')
    def test_get_rated_movies_missing_tmdb_id(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'movie': {
                    'title': 'Test Movie',
                    'year': 2023,
                    'ids': {'trakt': 1}  # No tmdb_id
                },
                'rating': 8,
                'rated_at': '2023-01-01T00:00:00Z'
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        results = get_rated_movies('test_user', 'fake_client_id')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Movie')
        self.assertIsNone(results[0]['tmdb_id'])