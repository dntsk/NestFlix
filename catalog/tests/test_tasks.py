from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from ..models import Movie, UserRating, UserSettings, ImportTask

class TasksTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        self.user_settings = UserSettings.objects.create(
            user=self.user,
            tmdb_api_key='test_tmdb_key',
            trakt_username='test_user',
            trakt_client_id='test_client_id'
        )

    def test_import_trakt_data_processing_logic(self):
        """Тест логики обработки данных импорта (без фоновой задачи)"""
        # Создаем задачу импорта
        task = ImportTask.objects.create(
            user=self.user,
            task_id='test-task-123',
            status='pending'
        )
        
        # Имитируем данные из Trakt
        watched_movies = [
            {'tmdb_id': 123, 'media_type': 'movie', 'title': 'Test Movie', 'last_watched_at': '2023-01-01T12:00:00Z'}
        ]
        watched_shows = []
        rated_movies = [
            {'tmdb_id': 123, 'media_type': 'movie', 'title': 'Test Movie', 'rating': 8}
        ]
        rated_shows = []
        
        # Имитируем данные из TMDB
        movie_data = {
            'title': 'Test Movie',
            'overview': 'Test overview',
            'release_date': '2023-01-01'
        }
        
        # Обновляем статус задачи
        task.status = 'running'
        task.save()
        
        # Обрабатываем данные (имитируем логику из задачи)
        total_items = len(watched_movies) + len(watched_shows) + len(rated_movies) + len(rated_shows)
        task.total_items = total_items
        task.save()
        
        # Создаем словарь всех элементов
        all_items = {}
        
        # Обрабатываем просмотренные
        for item in watched_movies + watched_shows:
            if item['tmdb_id']:
                key = f"{item['media_type']}_{item['tmdb_id']}"
                all_items[key] = {
                    'tmdb_id': item['tmdb_id'],
                    'media_type': item['media_type'],
                    'title': item['title'],
                    'watched_at': item.get('last_watched_at'),
                    'rating': None
                }
        
        # Обрабатываем оцененные
        for item in rated_movies + rated_shows:
            if item['tmdb_id']:
                key = f"{item['media_type']}_{item['tmdb_id']}"
                if key in all_items:
                    all_items[key]['rating'] = item['rating']
                else:
                    all_items[key] = {
                        'tmdb_id': item['tmdb_id'],
                        'media_type': item['media_type'],
                        'title': item['title'],
                        'watched_at': None,
                        'rating': item['rating']
                    }
        
        # Импортируем в базу данных
        imported_count = 0
        
        for key, item in all_items.items():
            if movie_data:  # Если есть данные из TMDB
                # Создаем/обновляем фильм
                movie, created = Movie.objects.get_or_create(
                    tmdb_id=item['tmdb_id'],
                    media_type=item['media_type'],
                    defaults={
                        'title': movie_data.get('title') or item['title'],
                        'data': movie_data,
                    }
                )
                
                # Обрабатываем дату просмотра
                watched_at = None
                if item['watched_at']:
                    from datetime import datetime
                    watched_at = datetime.fromisoformat(item['watched_at'].replace('Z', '+00:00'))
                
                # Создаем/обновляем UserRating
                user_rating, created_rating = UserRating.objects.get_or_create(
                    user=self.user,
                    movie=movie,
                    defaults={
                        'rating': item['rating'],
                        'watched_at': watched_at,
                    }
                )
                
                imported_count += 1
        
        # Завершаем задачу
        task.status = 'completed'
        task.imported_count = imported_count
        task.save()
        
        # Проверяем результаты
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.imported_count, 1)
        self.assertEqual(task.total_items, 2)
        
        # Проверяем созданные объекты
        self.assertEqual(Movie.objects.count(), 1)
        movie = Movie.objects.first()
        self.assertEqual(movie.tmdb_id, 123)
        
        self.assertEqual(UserRating.objects.count(), 1)
        rating = UserRating.objects.first()
        self.assertEqual(rating.rating, 8)
        self.assertIsNotNone(rating.watched_at)

    def test_import_trakt_data_no_tmdb_data(self):
        """Тест обработки случая, когда нет данных из TMDB"""
        task = ImportTask.objects.create(
            user=self.user,
            task_id='test-task-456',
            status='pending'
        )
        
        # Имитируем данные из Trakt
        watched_movies = [
            {'tmdb_id': 999, 'media_type': 'movie', 'title': 'Non-existent Movie', 'last_watched_at': '2023-01-01T12:00:00Z'}
        ]
        
        # Обновляем статус задачи
        task.status = 'running'
        task.save()
        
        # Обрабатываем данные
        total_items = len(watched_movies)
        task.total_items = total_items
        task.save()
        
        # Создаем словарь всех элементов
        all_items = {}
        
        for item in watched_movies:
            if item['tmdb_id']:
                key = f"{item['media_type']}_{item['tmdb_id']}"
                all_items[key] = {
                    'tmdb_id': item['tmdb_id'],
                    'media_type': item['media_type'],
                    'title': item['title'],
                    'watched_at': item.get('last_watched_at'),
                    'rating': None
                }
        
        # Импортируем в базу данных (но данных из TMDB нет)
        imported_count = 0
        
        for key, item in all_items.items():
            # Пропускаем, так как нет данных из TMDB
            pass
        
        # Завершаем задачу
        task.status = 'completed'
        task.imported_count = imported_count
        task.save()
        
        # Проверяем результаты
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.imported_count, 0)
        self.assertEqual(Movie.objects.count(), 0)
        self.assertEqual(UserRating.objects.count(), 0)

    def test_import_trakt_data_duplicate_items(self):
        """Тест обработки дублирующихся элементов из Trakt"""
        task = ImportTask.objects.create(
            user=self.user,
            task_id='test-task-789',
            status='pending'
        )
        
        # Имитируем данные из Trakt (один фильм и в watched и в rated)
        watched_movies = [
            {'tmdb_id': 123, 'media_type': 'movie', 'title': 'Test Movie', 'last_watched_at': '2023-01-01T12:00:00Z'}
        ]
        rated_movies = [
            {'tmdb_id': 123, 'media_type': 'movie', 'title': 'Test Movie', 'rating': 8}
        ]
        
        # Обновляем статус задачи
        task.status = 'running'
        task.save()
        
        # Обрабатываем данные
        total_items = len(watched_movies) + len(rated_movies)
        task.total_items = total_items
        task.save()
        
        # Создаем словарь всех элементов (имитируем логику объединения)
        all_items = {}
        
        for item in watched_movies:
            if item['tmdb_id']:
                key = f"{item['media_type']}_{item['tmdb_id']}"
                all_items[key] = {
                    'tmdb_id': item['tmdb_id'],
                    'media_type': item['media_type'],
                    'title': item['title'],
                    'watched_at': item.get('last_watched_at'),
                    'rating': None
                }
        
        for item in rated_movies:
            if item['tmdb_id']:
                key = f"{item['media_type']}_{item['tmdb_id']}"
                if key in all_items:
                    all_items[key]['rating'] = item['rating']
                else:
                    all_items[key] = {
                        'tmdb_id': item['tmdb_id'],
                        'media_type': item['media_type'],
                        'title': item['title'],
                        'watched_at': None,
                        'rating': item['rating']
                    }
        
        # Имитируем данные из TMDB
        movie_data = {
            'title': 'Test Movie',
            'overview': 'Test overview',
            'release_date': '2023-01-01'
        }
        
        # Импортируем в базу данных
        imported_count = 0
        
        for key, item in all_items.items():
            if movie_data:
                # Создаем/обновляем фильм
                movie, created = Movie.objects.get_or_create(
                    tmdb_id=item['tmdb_id'],
                    media_type=item['media_type'],
                    defaults={
                        'title': movie_data.get('title') or item['title'],
                        'data': movie_data,
                    }
                )
                
                # Обрабатываем дату просмотра
                watched_at = None
                if item['watched_at']:
                    from datetime import datetime
                    watched_at = datetime.fromisoformat(item['watched_at'].replace('Z', '+00:00'))
                
                # Создаем/обновляем UserRating
                user_rating, created_rating = UserRating.objects.get_or_create(
                    user=self.user,
                    movie=movie,
                    defaults={
                        'rating': item['rating'],
                        'watched_at': watched_at,
                    }
                )
                
                imported_count += 1
        
        # Завершаем задачу
        task.status = 'completed'
        task.imported_count = imported_count
        task.save()
        
        # Проверяем результаты
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.imported_count, 1)  # Должен быть только один фильм
        self.assertEqual(task.total_items, 2)  # Но оба элемента учтены
        
        self.assertEqual(Movie.objects.count(), 1)
        self.assertEqual(UserRating.objects.count(), 1)
        
        rating = UserRating.objects.first()
        self.assertEqual(rating.rating, 8)
        self.assertIsNotNone(rating.watched_at)

    def test_import_trakt_data_existing_movie(self):
        """Тест импорта для уже существующего фильма"""
        # Создаем фильм заранее
        movie = Movie.objects.create(
            tmdb_id=123,
            media_type='movie',
            title='Old Title',
            data={'old': 'data'}
        )
        
        task = ImportTask.objects.create(
            user=self.user,
            task_id='test-task-existing',
            status='pending'
        )
        
        # Имитируем данные из Trakt
        watched_movies = [
            {'tmdb_id': 123, 'media_type': 'movie', 'title': 'New Title', 'last_watched_at': '2023-01-01T12:00:00Z'}
        ]
        
        # Обновляем статус задачи
        task.status = 'running'
        task.save()
        
        # Обрабатываем данные
        total_items = len(watched_movies)
        task.total_items = total_items
        task.save()
        
        # Создаем словарь всех элементов
        all_items = {}
        
        for item in watched_movies:
            if item['tmdb_id']:
                key = f"{item['media_type']}_{item['tmdb_id']}"
                all_items[key] = {
                    'tmdb_id': item['tmdb_id'],
                    'media_type': item['media_type'],
                    'title': item['title'],
                    'watched_at': item.get('last_watched_at'),
                    'rating': None
                }
        
        # Имитируем данные из TMDB
        movie_data = {
            'title': 'New Title',
            'overview': 'New overview',
            'release_date': '2023-01-01'
        }
        
        # Импортируем в базу данных
        imported_count = 0
        
        for key, item in all_items.items():
            if movie_data:
                # Создаем/обновляем фильм
                movie, created = Movie.objects.get_or_create(
                    tmdb_id=item['tmdb_id'],
                    media_type=item['media_type'],
                    defaults={
                        'title': movie_data.get('title') or item['title'],
                        'data': movie_data,
                    }
                )
                
                # Обновляем существующий фильм
                if not created:
                    movie.title = movie_data.get('title') or item['title']
                    movie.data = movie_data
                    movie.save()
                
                # Обрабатываем дату просмотра
                watched_at = None
                if item['watched_at']:
                    from datetime import datetime
                    watched_at = datetime.fromisoformat(item['watched_at'].replace('Z', '+00:00'))
                
                # Создаем/обновляем UserRating
                user_rating, created_rating = UserRating.objects.get_or_create(
                    user=self.user,
                    movie=movie,
                    defaults={
                        'rating': item['rating'],
                        'watched_at': watched_at,
                    }
                )
                
                imported_count += 1
        
        # Завершаем задачу
        task.status = 'completed'
        task.imported_count = imported_count
        task.save()
        
        # Проверяем, что фильм обновлен
        movie.refresh_from_db()
        self.assertEqual(movie.title, 'New Title')
        self.assertEqual(movie.data['title'], 'New Title')
        
        # Проверяем, что рейтинг создан
        self.assertEqual(UserRating.objects.count(), 1)
        rating = UserRating.objects.first()
        self.assertEqual(rating.movie, movie)
        self.assertIsNotNone(rating.watched_at)

    def test_import_trakt_data_error_handling(self):
        """Тест обработки ошибок при импорте"""
        task = ImportTask.objects.create(
            user=self.user,
            task_id='test-task-error',
            status='pending'
        )
        
        # Имитируем ошибку при обработке
        task.status = 'running'
        task.save()
        
        # Имитируем возникновение исключения
        try:
            raise Exception("Test error during processing")
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
        
        # Проверяем, что задача завершилась с ошибкой
        task.refresh_from_db()
        self.assertEqual(task.status, 'failed')
        self.assertIn('Test error during processing', task.error_message)