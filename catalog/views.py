from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.core.paginator import Paginator
from datetime import datetime
from .models import Movie, UserRating, UserSettings, ImportTask
from .tmdb_client import search_movies, get_movie_details
from .trakt_client import get_watched_movies, get_watched_shows, get_rated_movies, get_rated_shows
from .tasks import import_trakt_data_task
import time
import re
from django.contrib import messages

@login_required
def movie_search(request):
    # Get user settings for TMDB API key
    try:
        settings_obj = UserSettings.objects.get(user=request.user)
        tmdb_api_key = settings_obj.tmdb_api_key
    except UserSettings.DoesNotExist:
        tmdb_api_key = None

    if not tmdb_api_key:
        return render(request, 'catalog/search.html', {'error': 'Настройте TMDB API Key в разделе настроек'})

    if request.META.get('HTTP_HX_REQUEST') and 'query' in request.GET:
        query = request.GET.get('query')
        if query:
            results = search_movies(query, tmdb_api_key)
            # Add is_in_collection flag
            for result in results:
                movie_exists = Movie.objects.filter(tmdb_id=result['id']).exists()
                if movie_exists:
                    movie = Movie.objects.get(tmdb_id=result['id'])
                    result['is_in_collection'] = UserRating.objects.filter(user=request.user, movie=movie).exists()
                else:
                    result['is_in_collection'] = False
            return render(request, 'catalog/partials/search_results.html', {'results': results})
        else:
            return render(request, 'catalog/partials/search_results.html', {'results': []})
    return render(request, 'catalog/search.html')

@login_required
def add_movie(request, media_type, tmdb_id):
    # Get user settings for TMDB API key
    try:
        settings_obj = UserSettings.objects.get(user=request.user)
        tmdb_api_key = settings_obj.tmdb_api_key
    except UserSettings.DoesNotExist:
        return HttpResponse('<p>Настройте TMDB API Key в разделе настроек</p>', status=400)

    if not tmdb_api_key:
        return HttpResponse('<p>Настройте TMDB API Key в разделе настроек</p>', status=400)

    if request.method in ['POST', 'PUT']:
        movie_data = get_movie_details(media_type, tmdb_id, tmdb_api_key)
        if not movie_data:
            return HttpResponse('<p>Ошибка загрузки данных.</p>', status=500)
        title = movie_data.get('title', movie_data.get('name', 'Unknown'))
        movie, created = Movie.objects.get_or_create(
            tmdb_id=tmdb_id,
            media_type=media_type,
            defaults={
                'title': title,
                'data': movie_data,
            }
        )
        if not created:
            movie.data = movie_data
            movie.save()
        # Create UserRating if not exists
        UserRating.objects.get_or_create(user=request.user, movie=movie)
        return HttpResponse('<p>Успешно добавлено!</p>')
    return HttpResponse('Ошибка', status=400)

@login_required
def movie_detail(request, tmdb_id):
    movie = get_object_or_404(Movie, tmdb_id=tmdb_id)
    user_rating, created = UserRating.objects.get_or_create(user=request.user, movie=movie)

    # Get user settings for TMDB API key (for future use if needed)
    try:
        settings_obj = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        settings_obj = None

    if request.method == 'POST':
        rating = request.POST.get('rating')
        if rating:
            user_rating.rating = int(rating)
            user_rating.save()
            messages.success(request, 'Оценка обновлена!')
            return redirect('catalog:movie_detail', tmdb_id=tmdb_id)
    # Prepare data for template
    data = movie.data or {}
    title = data.get('title', data.get('name', movie.title))
    release_date = data.get('release_date', data.get('first_air_date', ''))
    overview = data.get('overview', '')
    poster_path = data.get('poster_path', '')
    vote_average = data.get('vote_average', '')
    context = {
        'movie': movie,
        'user_rating': user_rating,
        'title': title,
        'release_date': release_date,
        'overview': overview,
        'poster_path': poster_path,
        'vote_average': vote_average,
    }
    return render(request, 'catalog/movie_detail.html', context)

def my_library(request):
    if request.user.is_authenticated:
        # Показываем личную коллекцию авторизованного пользователя
        user_ratings = UserRating.objects.filter(user=request.user).select_related('movie').order_by('-watched_at', '-created_at')
        paginator = Paginator(user_ratings, 20)  # 20 items per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'catalog/my_library.html', {
            'page_obj': page_obj,
            'is_authenticated': True
        })
    else:
        # Показываем публичный список фильмов для неавторизованных пользователей
        # Берем фильмы отсортированные по дате последнего просмотра
        from django.db.models import Avg, Count, Max
        movies_with_ratings = Movie.objects.annotate(
            avg_rating=Avg('userrating__rating'),
            rating_count=Count('userrating'),
            last_watched=Max('userrating__watched_at')
        ).filter(rating_count__gt=0).order_by('-last_watched')[:20]  # Топ 20 недавно просмотренных фильмов

        return render(request, 'catalog/public_library.html', {
            'movies': movies_with_ratings,
            'is_authenticated': False
        })

@login_required
def user_settings(request):
    settings_obj, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Валидация и санитизация входных данных
        tmdb_api_key = request.POST.get('tmdb_api_key', '').strip()
        trakt_username = request.POST.get('trakt_username', '').strip()
        trakt_client_id = request.POST.get('trakt_client_id', '').strip()
        
        # Проверка формата API ключей
        if tmdb_api_key and len(tmdb_api_key) != 32:
            messages.error(request, 'TMDB API Key должен содержать 32 символа')
            return redirect('catalog:user_settings')
            
        if trakt_client_id and len(trakt_client_id) != 64:
            messages.error(request, 'Trakt Client ID должен содержать 64 символа')
            return redirect('catalog:user_settings')
            
        # Санитизация username - только буквы, цифры, дефисы и подчеркивания
        if trakt_username and not re.match(r'^[a-zA-Z0-9_-]+$', trakt_username):
            messages.error(request, 'Trakt username содержит недопустимые символы')
            return redirect('catalog:user_settings')

        settings_obj.tmdb_api_key = tmdb_api_key
        settings_obj.trakt_username = trakt_username
        settings_obj.trakt_client_id = trakt_client_id
        settings_obj.save()
        messages.success(request, 'Настройки сохранены!')
        return redirect('catalog:user_settings')

    return render(request, 'catalog/user_settings.html', {'settings': settings_obj})

@login_required
def import_from_trakt(request):
    """Запуск импорта в фоне"""
    # Get user settings
    try:
        settings_obj = UserSettings.objects.get(user=request.user)
        username = settings_obj.trakt_username
        trakt_client_id = settings_obj.trakt_client_id
        tmdb_key = settings_obj.tmdb_api_key
    except UserSettings.DoesNotExist:
        if request.META.get('HTTP_HX_REQUEST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Сначала настройте API ключи'}, status=400)
        messages.error(request, 'Сначала настройте API ключи')
        return redirect('catalog:user_settings')

    if not all([username, trakt_client_id, tmdb_key]):
        if request.META.get('HTTP_HX_REQUEST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Заполните все API настройки'}, status=400)
        messages.error(request, 'Заполните все API настройки')
        return redirect('catalog:user_settings')

    # Проверяем, есть ли уже активная задача импорта для этого пользователя
    active_tasks = ImportTask.objects.filter(
        user=request.user,
        status__in=['pending', 'running']
    ).exists()

    if active_tasks:
        if request.META.get('HTTP_HX_REQUEST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Импорт уже запущен. Дождитесь завершения текущей задачи.'
            }, status=400)
        messages.warning(request, 'Импорт уже запущен. Дождитесь завершения текущей задачи.')
        return redirect('catalog:user_settings')

    # Создаем запись о задаче
    task_id = f"import_{request.user.id}_{int(time.time())}"
    task = ImportTask.objects.create(
        user=request.user,
        task_id=task_id,
        status='pending'
    )

    print(f"Starting import task {task_id} for user {request.user.username}")
    print(f"Trakt settings: username='{username}', client_id='{trakt_client_id[:4]}...{trakt_client_id[-4:]}'")

    # Запускаем фоновую задачу
    import_trakt_data_task(
        task_id=task_id,
        user_id=request.user.id,
        username=username,
        client_id=trakt_client_id,
        tmdb_key=tmdb_key
    )

    # Проверяем, AJAX ли запрос
    if request.META.get('HTTP_HX_REQUEST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'task_id': task_id,
            'status': 'started',
            'message': 'Импорт запущен в фоне'
        })

    messages.success(request, 'Импорт запущен в фоне. Вы получите уведомление по завершении.')
    return redirect('catalog:user_settings')

@login_required
def import_status(request, task_id):
    """Получение статуса импорта"""
    try:
        task = ImportTask.objects.get(task_id=task_id, user=request.user)
        data = {
            'status': task.status,
            'progress': task.progress,
            'imported_count': task.imported_count,
            'total_items': task.total_items,
            'error_message': task.error_message,
        }
        return JsonResponse(data)
    except ImportTask.DoesNotExist:
        return JsonResponse({'error': 'Задача не найдена'}, status=404)

    context = {
        'saved_username': request.session.get('trakt_username', ''),
    }
    return render(request, 'catalog/import_trakt.html', context)


def logout_view(request):
    logout(request)
    return redirect('catalog:home')
