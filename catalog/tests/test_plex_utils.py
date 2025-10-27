from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from ..models import Movie, UserRating, UserSettings
from ..plex_utils import extract_tmdb_id_from_plex_guid, process_plex_event


class PlexUtilsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.user_settings = UserSettings.objects.create(
            user=self.user,
            tmdb_api_key='test_tmdb_key_32_characters_long_',
            language='en'
        )

    def test_extract_tmdb_id_simple_tmdb_format(self):
        guid = 'tmdb://12345'
        tmdb_id = extract_tmdb_id_from_plex_guid(guid)
        self.assertEqual(tmdb_id, 12345)

    def test_extract_tmdb_id_themoviedb_format(self):
        guid = 'com.plexapp.agents.themoviedb://67890?lang=en'
        tmdb_id = extract_tmdb_id_from_plex_guid(guid)
        self.assertEqual(tmdb_id, 67890)

    def test_extract_tmdb_id_from_guid_array(self):
        guid = 'plex://movie/5d776825880197001ec90e31'
        guid_list = [
            {'id': 'imdb://tt1234567'},
            {'id': 'tmdb://99999'},
            {'id': 'tvdb://111111'}
        ]
        tmdb_id = extract_tmdb_id_from_plex_guid(guid, guid_list)
        self.assertEqual(tmdb_id, 99999)

    def test_extract_tmdb_id_no_match(self):
        guid = 'plex://movie/5d776825880197001ec90e31'
        tmdb_id = extract_tmdb_id_from_plex_guid(guid)
        self.assertIsNone(tmdb_id)

    def test_extract_tmdb_id_empty_guid(self):
        tmdb_id = extract_tmdb_id_from_plex_guid('')
        self.assertIsNone(tmdb_id)

    def test_extract_tmdb_id_ignores_tvdb(self):
        guid = 'plex://show/5fd2a1b82de5fd002dd4c7b1'
        guid_list = [
            {'id': 'tvdb://5127547'},
            {'id': 'imdb://tt1234567'}
        ]
        tmdb_id = extract_tmdb_id_from_plex_guid(guid, guid_list)
        self.assertIsNone(tmdb_id)

    def test_extract_tmdb_id_prefers_tmdb_over_others(self):
        guid = 'plex://show/5fd2a1b82de5fd002dd4c7b1'
        guid_list = [
            {'id': 'tvdb://5127547'},
            {'id': 'tmdb://88888'},
            {'id': 'imdb://tt1234567'}
        ]
        tmdb_id = extract_tmdb_id_from_plex_guid(guid, guid_list)
        self.assertEqual(tmdb_id, 88888)

    @patch('catalog.plex_utils.get_movie_details')
    def test_process_plex_event_movie_scrobble(self, mock_get_details):
        mock_get_details.return_value = {
            'title': 'Test Movie',
            'overview': 'Test overview',
            'release_date': '2020-01-01'
        }

        payload = {
            'event': 'media.scrobble',
            'Metadata': {
                'type': 'movie',
                'guid': 'tmdb://12345',
                'title': 'Test Movie',
                'Guid': []
            }
        }

        result = process_plex_event(self.user, 'media.scrobble', payload)
        self.assertTrue(result)

        movie = Movie.objects.get(tmdb_id=12345)
        self.assertEqual(movie.title, 'Test Movie')
        self.assertEqual(movie.media_type, 'movie')

        user_rating = UserRating.objects.get(user=self.user, movie=movie)
        self.assertIsNotNone(user_rating.watched_at)

    @patch('catalog.plex_utils.get_movie_details')
    def test_process_plex_event_episode_with_guid_array(self, mock_get_details):
        mock_get_details.return_value = {
            'name': 'Test Show',
            'overview': 'Test overview',
            'first_air_date': '2020-01-01'
        }

        payload = {
            'event': 'media.scrobble',
            'Metadata': {
                'type': 'episode',
                'guid': 'plex://episode/65c2577ab267ed59cc12c5b3',
                'title': 'Episode 1',
                'grandparentGuid': 'plex://show/5d9c081c46115600200aa7d6',
                'grandparentTitle': 'Test Show',
                'Guid': [
                    {'id': 'imdb://tt1234567'},
                    {'id': 'tvdb://111111'},
                    {'id': 'tmdb://88888'}
                ]
            }
        }

        result = process_plex_event(self.user, 'media.scrobble', payload)
        self.assertTrue(result)

        movie = Movie.objects.get(tmdb_id=88888)
        self.assertEqual(movie.title, 'Test Show')
        self.assertEqual(movie.media_type, 'tv')

        user_rating = UserRating.objects.get(user=self.user, movie=movie)
        self.assertIsNotNone(user_rating.watched_at)

    @patch('catalog.plex_utils.get_movie_details')
    def test_process_plex_event_episode_without_tmdb_id(self, mock_get_details):
        payload = {
            'event': 'media.scrobble',
            'Metadata': {
                'type': 'episode',
                'guid': 'plex://episode/65c2577ab267ed59cc12c5b3',
                'title': 'Episode 1',
                'grandparentGuid': 'plex://show/5d9c081c46115600200aa7d6',
                'grandparentTitle': 'Test Show',
                'Guid': []
            }
        }

        result = process_plex_event(self.user, 'media.scrobble', payload)
        self.assertFalse(result)
        mock_get_details.assert_not_called()

    @patch('catalog.plex_utils.get_movie_details')
    def test_process_plex_event_play_adds_to_collection(self, mock_get_details):
        mock_get_details.return_value = {
            'title': 'Test Movie',
            'overview': 'Test overview'
        }

        payload = {
            'event': 'media.play',
            'Metadata': {
                'type': 'movie',
                'guid': 'tmdb://54321',
                'title': 'Test Movie',
                'Guid': []
            }
        }

        result = process_plex_event(self.user, 'media.play', payload)
        self.assertTrue(result)

        movie = Movie.objects.get(tmdb_id=54321)
        user_rating = UserRating.objects.get(user=self.user, movie=movie)
        self.assertIsNone(user_rating.watched_at)

    def test_process_plex_event_ignored_event(self):
        payload = {
            'event': 'media.pause',
            'Metadata': {
                'type': 'movie',
                'guid': 'tmdb://11111'
            }
        }

        result = process_plex_event(self.user, 'media.pause', payload)
        self.assertFalse(result)

    @patch('catalog.plex_utils.get_movie_details')
    def test_process_plex_event_updates_watched_date(self, mock_get_details):
        from django.utils import timezone
        from datetime import timedelta
        
        mock_get_details.return_value = {
            'title': 'Test Movie',
            'overview': 'Test overview'
        }

        # First scrobble
        payload = {
            'event': 'media.scrobble',
            'Metadata': {
                'type': 'movie',
                'guid': 'tmdb://99999',
                'title': 'Test Movie',
                'Guid': []
            }
        }

        result = process_plex_event(self.user, 'media.scrobble', payload)
        self.assertTrue(result)

        movie = Movie.objects.get(tmdb_id=99999)
        user_rating = UserRating.objects.get(user=self.user, movie=movie)
        first_watched_at = user_rating.watched_at
        self.assertIsNotNone(first_watched_at)

        # Second scrobble (simulate watching again later)
        import time
        time.sleep(0.1)  # Small delay to ensure different timestamp
        
        result = process_plex_event(self.user, 'media.scrobble', payload)
        self.assertTrue(result)

        user_rating.refresh_from_db()
        second_watched_at = user_rating.watched_at
        self.assertIsNotNone(second_watched_at)
        self.assertGreater(second_watched_at, first_watched_at)

    @patch('catalog.plex_utils.get_movie_details')
    def test_process_plex_event_uses_user_language(self, mock_get_details):
        mock_get_details.return_value = {
            'title': 'Тестовый Фильм',
            'overview': 'Описание на русском'
        }
        
        # Set user language to Russian
        self.user_settings.language = 'ru'
        self.user_settings.save()

        payload = {
            'event': 'media.scrobble',
            'Metadata': {
                'type': 'movie',
                'guid': 'tmdb://12345',
                'title': 'Test Movie',
                'Guid': []
            }
        }

        result = process_plex_event(self.user, 'media.scrobble', payload)
        self.assertTrue(result)

        # Verify that get_movie_details was called with Russian language
        mock_get_details.assert_called_once_with(
            'movie', 
            12345, 
            'test_tmdb_key_32_characters_long_',
            'ru-RU'  # Russian language code for TMDB
        )

    @patch('catalog.plex_utils.get_movie_details')
    def test_process_plex_event_no_tmdb_api_key(self, mock_get_details):
        self.user_settings.tmdb_api_key = ''
        self.user_settings.save()

        payload = {
            'event': 'media.scrobble',
            'Metadata': {
                'type': 'movie',
                'guid': 'tmdb://99999',
                'Guid': []
            }
        }

        result = process_plex_event(self.user, 'media.scrobble', payload)
        self.assertFalse(result)
        mock_get_details.assert_not_called()
