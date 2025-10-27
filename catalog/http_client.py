import requests
from django.conf import settings
from .logger import logger


def get_proxies():
    """
    Get configured proxies for requests.
    
    Returns:
        dict or None: Proxies configuration or None if disabled
    """
    if settings.PROXY_ENABLED and settings.PROXIES:
        proxy_list = ', '.join([f"{k}: {v}" for k, v in settings.PROXIES.items()])
        logger.debug(f"Using proxy: {proxy_list}")
        return settings.PROXIES
    return None


def requests_get(*args, **kwargs):
    """
    Wrapper for requests.get with automatic proxy support.
    
    All arguments are passed through to requests.get().
    Automatically adds proxies if PROXY_ENABLED=True.
    
    Returns:
        requests.Response: Response object from requests.get()
    """
    proxies = get_proxies()
    if proxies:
        kwargs['proxies'] = proxies
    return requests.get(*args, **kwargs)
