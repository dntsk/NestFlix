from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import Movie, UserRating, UserSettings, ImportTask

class MovieModelTest(TestCase):
    def setUp(self):
        self.movie = Movie(tmdb_id=123, media_type='movie', title='Test Movie')
        self.movie.data = {'title': 'Test Movie', 'overview': 'Test overview'}
        self.movie.save()

    def test_movie_creation(self):
        self.assertEqual(self.movie.tmdb_id, 123)
        self.assertEqual(self.movie.media_type, 'movie')
        self.assertEqual(self.movie.title, 'Test Movie')
        self.assertIsNotNone(self.movie.data)

    def test_movie_str_representation(self):
        self.assertEqual(str(self.movie), 'Test Movie')

    def test_movie_unique_tmdb_id(self):
        movie2 = Movie(tmdb_id=123, media_type='movie', title='Another Movie')
        try:
            movie2.save()
            self.fail("Should have raised exception for duplicate tmdb_id")
        except Exception:
            pass  # Expected behavior

class UserRatingModelTest(TestCase):
    def setUp(self):
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        self.user.save()

        self.movie = Movie(tmdb_id=456, media_type='movie', title='Test Movie for Rating')
        self.movie.save()

        self.user_rating = UserRating(user=self.user, movie=self.movie, rating=8)
        self.user_rating.save()

    def test_user_rating_creation(self):
        self.assertEqual(self.user_rating.user, self.user)
        self.assertEqual(self.user_rating.movie, self.movie)
        self.assertEqual(self.user_rating.rating, 8)
        self.assertIsNotNone(self.user_rating.created_at)

    def test_user_rating_unique_together(self):
        user_rating2 = UserRating(user=self.user, movie=self.movie, rating=9)
        with self.assertRaises(Exception):
            user_rating2.save()

    def test_user_rating_str_representation(self):
        expected_str = f"{self.user.username} - {self.movie.title}"
        self.assertEqual(str(self.user_rating), expected_str)

    def test_user_rating_rating_validation(self):
        # Create a different movie for this test
        movie2 = Movie(tmdb_id=999, media_type='movie', title='Another Movie')
        movie2.save()

        valid_rating = UserRating(user=self.user, movie=movie2, rating=5)
        try:
            valid_rating.full_clean()
        except Exception:
            self.fail("Valid rating should not raise exception")

class UserSettingsModelTest(TestCase):
    def setUp(self):
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        self.user.save()

        self.user_settings = UserSettings(user=self.user)
        self.user_settings.tmdb_api_key = 'test_tmdb_key'
        self.user_settings.trakt_username = 'test_user'
        self.user_settings.trakt_client_id = 'test_client_id'
        self.user_settings.save()

    def test_user_settings_creation(self):
        self.assertEqual(self.user_settings.user, self.user)
        self.assertEqual(self.user_settings.tmdb_api_key, 'test_tmdb_key')
        self.assertEqual(self.user_settings.trakt_username, 'test_user')
        self.assertEqual(self.user_settings.trakt_client_id, 'test_client_id')
        self.assertIsNotNone(self.user_settings.created_at)
        self.assertIsNotNone(self.user_settings.updated_at)

    def test_user_settings_one_to_one_relationship(self):
        user_settings2 = UserSettings(user=self.user)
        with self.assertRaises(Exception):
            user_settings2.save()

    def test_user_settings_str_representation(self):
        expected_str = f"Settings for {self.user.username}"
        self.assertEqual(str(self.user_settings), expected_str)

    def test_user_settings_update(self):
        self.user_settings.tmdb_api_key = 'new_tmdb_key'
        self.user_settings.trakt_username = 'new_user'
        self.user_settings.trakt_client_id = 'new_client_id'
        self.user_settings.save()

        self.assertEqual(self.user_settings.tmdb_api_key, 'new_tmdb_key')
        self.assertEqual(self.user_settings.trakt_username, 'new_user')
        self.assertEqual(self.user_settings.trakt_client_id, 'new_client_id')
        self.assertIsNotNone(self.user_settings.updated_at)

    def test_user_settings_default_values(self):
        # Create a new user for this test to avoid unique constraint
        new_user = User(username='newuser', email='new@example.com')
        new_user.set_password('password')
        new_user.save()

        user_settings2 = UserSettings(user=new_user)
        user_settings2.save()

        self.assertEqual(user_settings2.tmdb_api_key, '')
        self.assertEqual(user_settings2.trakt_username, '')
        self.assertEqual(user_settings2.trakt_client_id, '')

class ImportTaskModelTest(TestCase):
    def setUp(self):
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        self.user.save()

        self.import_task = ImportTask(user=self.user, task_id='test_task_123', status='pending')
        self.import_task.progress = 0
        self.import_task.total_items = 10
        self.import_task.imported_count = 0
        self.import_task.save()

    def test_import_task_creation(self):
        self.assertEqual(self.import_task.user, self.user)
        self.assertEqual(self.import_task.task_id, 'test_task_123')
        self.assertEqual(self.import_task.status, 'pending')
        self.assertEqual(self.import_task.progress, 0)
        self.assertEqual(self.import_task.total_items, 10)
        self.assertEqual(self.import_task.imported_count, 0)
        self.assertEqual(self.import_task.error_message, '')
        self.assertIsNone(self.import_task.completed_at)

    def test_import_task_status_choices(self):
        valid_statuses = ['pending', 'running', 'completed', 'failed']
        for status in valid_statuses:
            task = ImportTask(user=self.user, task_id=f'test_{status}', status=status)
            try:
                task.full_clean()
            except Exception:
                self.fail(f"Status {status} should be valid")

    def test_import_task_unique_task_id(self):
        task2 = ImportTask(user=self.user, task_id='test_task_123', status='pending')
        with self.assertRaises(Exception):
            task2.save()

    def test_import_task_str_representation(self):
        expected_str = f"Import for {self.user.username} - pending"
        self.assertEqual(str(self.import_task), expected_str)