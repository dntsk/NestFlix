from django.contrib import admin
from .models import Movie, UserRating, UserSettings, ImportTask, PlexWebhookEvent

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
    list_display = ('user', 'tmdb_api_key_masked', 'trakt_username', 'trakt_client_id_masked', 'plex_webhook_enabled', 'updated_at')
    list_filter = ('plex_webhook_enabled',)
    search_fields = ('user__username', 'trakt_username')
    readonly_fields = ('created_at', 'updated_at', 'plex_webhook_created_at', 'plex_webhook_token_masked')

@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'progress', 'imported_count', 'total_items', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'task_id')
    readonly_fields = ('task_id', 'created_at', 'updated_at', 'completed_at')

@admin.register(PlexWebhookEvent)
class PlexWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'processed', 'created_at')
    list_filter = ('event_type', 'processed', 'created_at')
    search_fields = ('user__username', 'event_type')
    readonly_fields = ('user', 'event_type', 'payload', 'processed', 'error_message', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
