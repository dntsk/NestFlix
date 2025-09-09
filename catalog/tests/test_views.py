import json
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse
from unittest.mock import patch, MagicMock
from ..models import Movie, UserRating, UserSettings, ImportTask

class ViewsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        self.user.save()

        self.movie = Movie(tmdb_id=123, media_type='movie', title='Test Movie')
        self.movie.save()

        self.user_settings = UserSettings(user=self.user)
        self.user_settings.tmdb_api_key = 'test_tmdb_key_32_characters_long_'
        self.user_settings.save()

    def _add_messages_to_request(self, request):
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    @patch('catalog.views.search_movies')
    def test_movie_search_without_api_key(self, mock_search):
        user_no_settings = User(username='nouser', email='no@example.com')
        user_no_settings.set_password('password')
        user_no_settings.save()

        request = self.factory.get('/search/')
        request.user = user_no_settings
        request = self._add_messages_to_request(request)

        from catalog.views import movie_search
        response = movie_search(request)

        self.assertEqual(response.status_code, 200)
        # The view returns the search page template, error is in context
        # We can't easily test template context with RequestFactory
        # So we just verify the page loads correctly

    @patch('catalog.views.search_movies')
    def test_movie_search_with_api_key(self, mock_search):
        mock_search.return_value = [{'id': 123, 'title': 'Test Movie', 'media_type': 'movie'}]

        request = self.factory.get('/search/?query=test')
        request.user = self.user
        request.META['HTTP_HX_REQUEST'] = 'true'

        from catalog.views import movie_search
        response = movie_search(request)

        self.assertEqual(response.status_code, 200)
        mock_search.assert_called_once_with('test', 'test_tmdb_key_32_characters_long_')

    @patch('catalog.views.get_movie_details')
    def test_add_movie_success(self, mock_get_details):
        mock_get_details.return_value = {'title': 'Test Movie', 'overview': 'Test'}

        request = self.factory.post('/add/movie/123/')
        request.user = self.user

        from catalog.views import add_movie
        response = add_movie(request, 'movie', 123)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Успешно добавлено!', response.content.decode())

    @patch('catalog.views.get_movie_details')
    def test_add_movie_no_api_key(self, mock_get_details):
        user_no_settings = User(username='nouser2', email='no2@example.com')
        user_no_settings.set_password('password')
        user_no_settings.save()

        request = self.factory.post('/add/movie/123/')
        request.user = user_no_settings

        from catalog.views import add_movie
        response = add_movie(request, 'movie', 123)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Настройте TMDB API Key', response.content.decode())

    def test_movie_detail_get(self):
        user_rating = UserRating(user=self.user, movie=self.movie)
        user_rating.save()

        request = self.factory.get(f'/movie/{self.movie.tmdb_id}/')
        request.user = self.user

        from catalog.views import movie_detail
        response = movie_detail(request, self.movie.tmdb_id)

        self.assertEqual(response.status_code, 200)

    def test_movie_detail_post_rating(self):
        user_rating = UserRating(user=self.user, movie=self.movie)
        user_rating.save()

        request = self.factory.post(f'/movie/{self.movie.tmdb_id}/', {'rating': '8'})
        request.user = self.user
        request = self._add_messages_to_request(request)

        from catalog.views import movie_detail
        response = movie_detail(request, self.movie.tmdb_id)

        self.assertEqual(response.status_code, 302)  # Redirect
        user_rating.refresh_from_db()
        self.assertEqual(user_rating.rating, 8)

    def test_my_library_authenticated(self):
        user_rating = UserRating(user=self.user, movie=self.movie)
        user_rating.save()

        request = self.factory.get('/my-library/')
        request.user = self.user

        from catalog.views import my_library
        response = my_library(request)

        self.assertEqual(response.status_code, 200)

    def test_my_library_anonymous(self):
        request = self.factory.get('/my-library/')
        request.user = AnonymousUser()

        from catalog.views import my_library
        response = my_library(request)

        self.assertEqual(response.status_code, 200)

    def test_user_settings_get(self):
        request = self.factory.get('/settings/')
        request.user = self.user

        from catalog.views import user_settings
        response = user_settings(request)

        self.assertEqual(response.status_code, 200)

    def test_user_settings_post(self):
        request = self.factory.post('/settings/', {
            'tmdb_api_key': 'new_tmdb_key_32_characters_long_',
            'trakt_username': 'new_user',
            'trakt_client_id': 'new_client_id_64_characters_long_1234567890123456789012345678901'
        })
        request.user = self.user
        request = self._add_messages_to_request(request)

        from catalog.views import user_settings
        response = user_settings(request)

        self.assertEqual(response.status_code, 302)  # Redirect
        self.user_settings.refresh_from_db()
        self.assertEqual(self.user_settings.tmdb_api_key, 'new_tmdb_key_32_characters_long_')

    @patch('catalog.views.import_trakt_data_task')
    def test_import_from_trakt_missing_settings(self, mock_import_task):
        user_no_settings = User(username='nouser3', email='no3@example.com')
        user_no_settings.set_password('password')
        user_no_settings.save()

        request = self.factory.post('/import/')
        request.user = user_no_settings
        request = self._add_messages_to_request(request)

        from catalog.views import import_from_trakt
        response = import_from_trakt(request)

        self.assertEqual(response.status_code, 302)  # Redirect to settings
        mock_import_task.assert_not_called()

    @patch('catalog.views.import_trakt_data_task')
    def test_import_from_trakt_success(self, mock_import_task):
        # Setup user with complete settings
        self.user_settings.trakt_username = 'test_user'
        self.user_settings.trakt_client_id = 'test_client_id'
        self.user_settings.save()

        request = self.factory.post('/import/')
        request.user = self.user
        request = self._add_messages_to_request(request)

        from catalog.views import import_from_trakt
        response = import_from_trakt(request)

        self.assertEqual(response.status_code, 302)  # Redirect
        mock_import_task.assert_called_once()

    @patch('catalog.views.import_trakt_data_task')
    def test_import_from_trakt_duplicate_task_blocked(self, mock_import_task):
        # Setup user with complete settings
        self.user_settings.trakt_username = 'test_user'
        self.user_settings.trakt_client_id = 'test_client_id'
        self.user_settings.save()

        # Create an active import task
        ImportTask.objects.create(
            user=self.user,
            task_id='existing_task',
            status='running'
        )

        request = self.factory.post('/import/')
        request.user = self.user
        request = self._add_messages_to_request(request)

        from catalog.views import import_from_trakt
        response = import_from_trakt(request)

        # Should redirect with warning message
        self.assertEqual(response.status_code, 302)
        mock_import_task.assert_not_called()

    @patch('catalog.views.import_trakt_data_task')
    def test_import_from_trakt_duplicate_task_ajax_blocked(self, mock_import_task):
        # Setup user with complete settings
        self.user_settings.trakt_username = 'test_user'
        self.user_settings.trakt_client_id = 'test_client_id'
        self.user_settings.save()

        # Create an active import task
        ImportTask.objects.create(
            user=self.user,
            task_id='existing_task',
            status='pending'
        )

        request = self.factory.post('/import/')
        request.user = self.user
        request.META['HTTP_HX_REQUEST'] = 'true'

        from catalog.views import import_from_trakt
        response = import_from_trakt(request)

        # Should return JSON error
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode())
        self.assertIn('error', response_data)
        self.assertIn('Импорт уже запущен', response_data['error'])
        mock_import_task.assert_not_called()

    @patch('catalog.views.import_trakt_data_task')
    def test_import_from_trakt_allowed_after_completion(self, mock_import_task):
        # Setup user with complete settings
        self.user_settings.trakt_username = 'test_user'
        self.user_settings.trakt_client_id = 'test_client_id'
        self.user_settings.save()

        # Create a completed import task
        ImportTask.objects.create(
            user=self.user,
            task_id='completed_task',
            status='completed'
        )

        request = self.factory.post('/import/')
        request.user = self.user
        request = self._add_messages_to_request(request)

        from catalog.views import import_from_trakt
        response = import_from_trakt(request)

        # Should allow new import after completion
        self.assertEqual(response.status_code, 302)
        mock_import_task.assert_called_once()

    def test_import_status(self):
        import_task = ImportTask(user=self.user, task_id='test_status', status='running')
        import_task.save()

        request = self.factory.get('/import-status/test_status/')
        request.user = self.user

        from catalog.views import import_status
        response = import_status(request, 'test_status')

        self.assertEqual(response.status_code, 200)
        response_data = response.content.decode()
        self.assertIn('running', response_data)

    def test_import_status_not_found(self):
        request = self.factory.get('/import-status/invalid_task/')
        request.user = self.user

        from catalog.views import import_status
        response = import_status(request, 'invalid_task')

        self.assertEqual(response.status_code, 404)
        response_data = response.content.decode()
        self.assertIn('error', response_data)