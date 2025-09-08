from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.my_library, name='home'),
    path('search/', views.movie_search, name='movie_search'),
    path('settings/', views.user_settings, name='user_settings'),
    path('import-trakt/', views.import_from_trakt, name='import_trakt'),
    path('import-status/<str:task_id>/', views.import_status, name='import_status'),
    path('add/<str:media_type>/<int:tmdb_id>/', views.add_movie, name='add_movie'),
    path('movie/<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
]