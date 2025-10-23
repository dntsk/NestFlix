from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.my_library, name='home'),
    path('search/', views.movie_search, name='movie_search'),
    path('settings/', views.user_settings, name='user_settings'),
    path('settings/generate-plex-webhook/', views.generate_plex_webhook, name='generate_plex_webhook'),
    path('settings/disable-plex-webhook/', views.disable_plex_webhook, name='disable_plex_webhook'),
    path('webhook/plex/<str:token>/', views.plex_webhook_receiver, name='plex_webhook'),
    path('import-trakt/', views.import_from_trakt, name='import_trakt'),
    path('import-status/<str:task_id>/', views.import_status, name='import_status'),
    path('add/<str:media_type>/<int:tmdb_id>/', views.add_movie, name='add_movie'),
    path('movie/<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
]