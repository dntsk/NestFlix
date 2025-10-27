from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def poster_url(movie, size='w300'):
    """
    Get poster URL with fallback logic:
    1. Local cache (if exists and not expired)
    2. TMDB CDN
    3. Placeholder image
    """
    if movie.poster_file and not movie.needs_poster_refresh():
        return movie.poster_file.url
    
    poster_path = movie.data.get('poster_path') if movie.data else None
    if poster_path:
        return f"https://image.tmdb.org/t/p/{size}{poster_path}"
    
    return settings.STATIC_URL + 'images/no-poster.png'


@register.inclusion_tag('catalog/partials/movie_poster.html')
def movie_poster(movie, size='w300', css_class=''):
    """
    Render movie poster with fallback logic and lazy loading
    """
    url = None
    
    if movie.poster_file and not movie.needs_poster_refresh():
        url = movie.poster_file.url
        source = 'cached'
    else:
        poster_path = movie.data.get('poster_path') if movie.data else None
        if poster_path:
            url = f"https://image.tmdb.org/t/p/{size}{poster_path}"
            source = 'tmdb'
        else:
            url = settings.STATIC_URL + 'images/no-poster.png'
            source = 'placeholder'
    
    title = movie.data.get('title', movie.data.get('name', movie.title)) if movie.data else movie.title
    
    return {
        'url': url,
        'title': title,
        'css_class': css_class,
        'source': source,
    }
