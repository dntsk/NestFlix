from background_task import background
from datetime import datetime
from django.utils import timezone
from .models import ImportTask, Movie, UserRating
from .trakt_client import get_watched_movies, get_watched_shows, get_rated_movies, get_rated_shows
from .tmdb_client import get_movie_details

@background(schedule=0)
def import_trakt_data_task(task_id, user_id, username, client_id, tmdb_key):
    """Фоновая задача импорта данных из Trakt.tv"""
    task = None
    try:
        print(f"Starting import task: {task_id}")
        print(f"Parameters: user_id={user_id}, username='{username}', client_id='{client_id[:10]}...', tmdb_key='{tmdb_key[:10]}...'")

        # Получаем задачу
        task = ImportTask.objects.get(task_id=task_id)
        task.status = 'running'
        task.save()

        # Получаем данные из Trakt
        print(f"Fetching data from Trakt for user: {username}")
        watched_movies = get_watched_movies(username, client_id)
        watched_shows = get_watched_shows(username, client_id)
        rated_movies = get_rated_movies(username, client_id)
        rated_shows = get_rated_shows(username, client_id)

        print(f"Trakt data received:")
        print(f"  Watched movies: {len(watched_movies)}")
        print(f"  Watched shows: {len(watched_shows)}")
        print(f"  Rated movies: {len(rated_movies)}")
        print(f"  Rated shows: {len(rated_shows)}")

        # Обновляем общее количество
        total_items = len(watched_movies) + len(watched_shows) + len(rated_movies) + len(rated_shows)
        task.total_items = total_items
        task.save()
        print(f"Total items to import: {total_items}")

        # Создаем словарь всех элементов
        all_items = {}
        processed_count = 0

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
            processed_count += 1
            task.progress = int((processed_count / total_items) * 50)  # 50% за обработку данных
            task.save()

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
            processed_count += 1
            # Прогресс остается в пределах 0-50% для фазы обработки данных
            task.progress = min(50, int((processed_count / total_items) * 50))
            task.save()

        # Импортируем в базу данных
        imported_count = 0
        total_to_import = len(all_items)

        print(f"Starting import of {total_to_import} items...")

        for i, (key, item) in enumerate(all_items.items()):
            try:
                movie_data = get_movie_details(item['media_type'], item['tmdb_id'], tmdb_key)
                if movie_data:
                    # Use TMDB title if available, otherwise keep Trakt title
                    final_title = movie_data.get('title') or movie_data.get('name') or item['title']
                    print(f"DEBUG Import: Trakt title: '{item['title']}', TMDB title: '{final_title}'")

                    movie, created = Movie.objects.get_or_create(
                        tmdb_id=item['tmdb_id'],
                        media_type=item['media_type'],
                        defaults={
                            'title': final_title,
                            'data': movie_data,
                        }
                    )

                    # ОБНОВЛЯЕМ существующую запись с новыми данными
                    if not created:
                        # Обновляем title если он отличается
                        if movie.title != final_title:
                            print(f"Updating title for {movie.title} -> {final_title}")
                            movie.title = final_title
                        movie.data = movie_data
                        movie.save()

                    # Обрабатываем дату просмотра
                    watched_at = None
                    if item['watched_at']:
                        try:
                            watched_at = datetime.fromisoformat(item['watched_at'].replace('Z', '+00:00'))
                        except ValueError:
                            pass

                    # Создаем/обновляем UserRating
                    user_rating, created_rating = UserRating.objects.get_or_create(
                        user_id=user_id,
                        movie=movie,
                        defaults={
                            'rating': item['rating'],
                            'watched_at': watched_at,
                        }
                    )

                    # ВАЖНО: Не переписываем существующую оценку!
                    # Только добавляем новую оценку, если её нет
                    if not created_rating:
                        # Если оценки нет в нашей базе, но есть в Trakt - добавляем
                        if user_rating.rating is None and item['rating'] is not None:
                            user_rating.rating = item['rating']
                            user_rating.save()
                        # Всегда обновляем дату просмотра, если её нет
                        if user_rating.watched_at is None and watched_at:
                            user_rating.watched_at = watched_at
                            user_rating.save()

                    # Считаем каждый обработанный элемент как импортированный
                    # Импорт - это процесс обработки всех элементов из Trakt
                    imported_count += 1

                    # Обновляем счетчик сразу после увеличения
                    task.imported_count = imported_count
                    task.save()
                    print(f"Imported {imported_count}/{total_to_import} items")

                    if created_rating:
                        print(f"Created new UserRating for {item['title']}")
                    elif user_rating.rating is None and item['rating'] is not None:
                        print(f"Updated rating for existing {item['title']}")
                    elif user_rating.watched_at is None and watched_at:
                        print(f"Updated watched_at for existing {item['title']}")
                    else:
                        print(f"Processed existing {item['title']} (no updates needed)")

                # Обновляем прогресс каждые 5 элементов или в конце
                if (i + 1) % 5 == 0 or (i + 1) == total_to_import:
                    progress = 50 + int(((i + 1) / total_to_import) * 50)
                    task.progress = min(100, progress)  # Не превышаем 100%
                    print(f"Import progress: {task.progress}% ({i + 1}/{total_to_import} processed, {imported_count} imported)")

            except Exception as e:
                print(f"Error importing {item['title']}: {e}")
                continue

        # Завершаем задачу
        task.status = 'completed'
        task.imported_count = imported_count
        task.completed_at = timezone.now()
        task.save()

    except ImportTask.DoesNotExist:
        print(f"Task {task_id} not found in database")
        # Задача была удалена, ничего не делаем
        return
    except Exception as e:
        print(f"Error in import task {task_id}: {e}")
        if task:
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
        else:
            print("Task object not available for error handling")