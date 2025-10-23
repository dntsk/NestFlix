import re
from django.utils import timezone
from .models import Movie, UserRating, UserSettings, PlexWebhookEvent
from .tmdb_client import get_movie_details
from .logger import logger


def extract_tmdb_id_from_plex_guid(guid):
    """
    Extract TMDB ID from Plex GUID
    
    Supported formats:
    - tmdb://123456
    - com.plexapp.agents.themoviedb://123456?lang=en
    - plex://movie/5d776825880197001ec90e31 (not supported, returns None)
    """
    if not guid:
        return None
    
    if guid.startswith('tmdb://'):
        match = re.search(r'tmdb://(\d+)', guid)
        if match:
            return int(match.group(1))
    
    if 'themoviedb' in guid:
        match = re.search(r'themoviedb://(\d+)', guid)
        if match:
            return int(match.group(1))
    
    logger.warning(f"Could not parse TMDB ID from Plex GUID: {guid}")
    return None


def process_plex_event(user, event, payload):
    """
    Process Plex webhook event and update database
    
    Supported events:
    - media.scrobble: Mark as watched
    - media.play: Add to collection
    """
    metadata = payload.get('Metadata', {})
    
    if event not in ['media.scrobble', 'media.play']:
        logger.debug(f"Ignoring Plex event: {event}")
        return False
    
    guid = metadata.get('guid', '')
    tmdb_id = extract_tmdb_id_from_plex_guid(guid)
    
    if not tmdb_id:
        logger.warning(f"Could not extract TMDB ID from guid: {guid}")
        return False
    
    media_type = metadata.get('type')
    title_from_plex = metadata.get('title', 'Unknown')
    
    if media_type == 'episode':
        media_type = 'tv'
        show_guid = metadata.get('grandparentGuid', '')
        extracted_show_id = extract_tmdb_id_from_plex_guid(show_guid)
        if extracted_show_id:
            tmdb_id = extracted_show_id
            title_from_plex = metadata.get('grandparentTitle', title_from_plex)
    elif media_type == 'movie':
        media_type = 'movie'
    else:
        logger.warning(f"Unknown Plex media type: {media_type}")
        return False
    
    try:
        settings = UserSettings.objects.get(user=user)
    except UserSettings.DoesNotExist:
        logger.error(f"UserSettings not found for user {user.username}")
        return False
    
    if not settings.tmdb_api_key:
        logger.warning(f"User {user.username} has no TMDB API key configured")
        return False
    
    movie_data = get_movie_details(media_type, tmdb_id, settings.tmdb_api_key)
    if not movie_data:
        logger.error(f"Could not fetch TMDB data for {media_type}/{tmdb_id}")
        return False
    
    title = movie_data.get('title') or movie_data.get('name') or title_from_plex
    
    movie, created = Movie.objects.get_or_create(
        tmdb_id=tmdb_id,
        media_type=media_type,
        defaults={
            'title': title,
            'data': movie_data
        }
    )
    
    if not created:
        movie.data = movie_data
        movie.title = title
        movie.save()
        logger.debug(f"Updated movie data: {title}")
    else:
        logger.info(f"Created new movie: {title}")
    
    if event == 'media.scrobble':
        user_rating, rating_created = UserRating.objects.get_or_create(
            user=user,
            movie=movie,
            defaults={'watched_at': timezone.now()}
        )
        
        if not rating_created and not user_rating.watched_at:
            user_rating.watched_at = timezone.now()
            user_rating.save()
            logger.info(f"Marked '{title}' as watched for {user.username}")
        elif rating_created:
            logger.info(f"Added '{title}' as watched for {user.username}")
        else:
            logger.debug(f"'{title}' already marked as watched for {user.username}")
            
    elif event == 'media.play':
        user_rating, rating_created = UserRating.objects.get_or_create(
            user=user,
            movie=movie
        )
        
        if rating_created:
            logger.info(f"Added '{title}' to collection for {user.username}")
        else:
            logger.debug(f"'{title}' already in collection for {user.username}")
    
    return True


def log_webhook_event(user, event_type, payload, processed=False, error_message=''):
    """
    Log Plex webhook event for audit purposes
    """
    try:
        PlexWebhookEvent.objects.create(
            user=user,
            event_type=event_type,
            payload=payload,
            processed=processed,
            error_message=error_message
        )
        logger.debug(f"Logged Plex webhook event: {event_type} for {user.username}")
    except Exception as e:
        logger.error(f"Failed to log webhook event: {e}")
