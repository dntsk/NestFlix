from django.utils import translation


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                user_settings = request.user.usersettings
                user_language = user_settings.language
                translation.activate(user_language)
                request.LANGUAGE_CODE = user_language
            except Exception:
                pass
        
        response = self.get_response(request)
        translation.deactivate()
        return response
