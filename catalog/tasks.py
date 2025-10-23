from background_task import background
from datetime import datetime
from django.utils import timezone
from .models import ImportTask, Movie, UserRating
from .trakt_client import get_watched_movies, get_watched_shows, get_rated_movies, get_rated_shows
from .tmdb_client import get_movie_details
from .logger import logger, mask_sensitive

@background(schedule=0)
def import_trakt_data_task(task_id, user_id, username, client_id, tmdb_key):
    """Фоновая задача импорта данных из Trakt.tv"""
    task = None
    try:
        logger.info(f"Starting import task: {task_id}")
        logger.debug(f"Parameters: user_id={user_id}, username='{username}', client_id={mask_sensitive(client_id)}, tmdb_key={mask_sensitive(tmdb_key)}")

        task = ImportTask.objects.get(task_id=task_id)
        task.status = 'running'
        task.save()
        logger.info(f"Task {task_id} status set to 'running'")

        logger.info(f"Fetching data from Trakt for user: {username}")
        watched_movies = get_watched_movies(username, client_id)
        watched_shows = get_watched_shows(username, client_id)
        rated_movies = get_rated_movies(username, client_id)
        rated_shows = get_rated_shows(username, client_id)

        logger.info(f"Trakt data received: {len(watched_movies)} watched movies, {len(watched_shows)} watched shows, {len(rated_movies)} rated movies, {len(rated_shows)} rated shows")

        total_items = len(watched_movies) + len(watched_shows) + len(rated_movies) + len(rated_shows)
        task.total_items = total_items
        task.save()
        logger.info(f"Total items to import: {total_items}")

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

        imported_count = 0
        total_to_import = len(all_items)

        logger.info(f"Starting import of {total_to_import} items into database")

        for i, (key, item) in enumerate(all_items.items()):
            try:
                movie_data = get_movie_details(item['media_type'], item['tmdb_id'], tmdb_key)
                if movie_data:
                    final_title = movie_data.get('title') or movie_data.get('name') or item['title']
                    logger.debug(f"Import item: Trakt='{item['title']}', TMDB='{final_title}'")

                    movie, created = Movie.objects.get_or_create(
                        tmdb_id=item['tmdb_id'],
                        media_type=item['media_type'],
                        defaults={
                            'title': final_title,
                            'data': movie_data,
                        }
                    )

                    if not created:
                        if movie.title != final_title:
                            logger.info(f"Updating title: {movie.title} -> {final_title}")
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

                    if not created_rating:
                        if user_rating.rating is None and item['rating'] is not None:
                            user_rating.rating = item['rating']
                            user_rating.save()
                            logger.debug(f"Updated rating for {item['title']}")
                        if user_rating.watched_at is None and watched_at:
                            user_rating.watched_at = watched_at
                            user_rating.save()
                            logger.debug(f"Updated watched_at for {item['title']}")
                    else:
                        logger.debug(f"Created new UserRating for {item['title']}")

                    imported_count += 1
                    task.imported_count = imported_count
                    task.save()

                if (i + 1) % 5 == 0 or (i + 1) == total_to_import:
                    progress = 50 + int(((i + 1) / total_to_import) * 50)
                    task.progress = min(100, progress)
                    logger.info(f"Import progress: {task.progress}% ({i + 1}/{total_to_import} processed, {imported_count} imported)")

            except Exception as e:
                logger.error(f"Error importing {item['title']}: {e}")
                continue

        task.status = 'completed'
        task.imported_count = imported_count
        task.completed_at = timezone.now()
        task.save()
        logger.info(f"Import task {task_id} completed successfully. Imported {imported_count} items.")

    except ImportTask.DoesNotExist:
        logger.warning(f"Task {task_id} not found in database")
        return
    except Exception as e:
        logger.error(f"Error in import task {task_id}: {e}")
        if task:
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
            logger.error(f"Task {task_id} marked as failed")
        else:
            logger.error("Task object not available for error handling")