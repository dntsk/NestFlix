from django.contrib import admin
from .models import Movie, UserRating, UserSettings, ImportTask

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'media_type', 'tmdb_id')
    list_filter = ('media_type',)
    search_fields = ('title', 'tmdb_id')
    readonly_fields = ('tmdb_id', 'data')
    ordering = ('title',)

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'watched_at', 'created_at')
    list_filter = ('rating', 'created_at', 'watched_at')
    search_fields = ('user__username', 'movie__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'tmdb_api_key', 'trakt_username', 'trakt_client_id', 'updated_at')
    search_fields = ('user__username', 'trakt_username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'progress', 'imported_count', 'total_items', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'task_id')
    readonly_fields = ('task_id', 'created_at', 'updated_at', 'completed_at')
