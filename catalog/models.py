from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True, primary_key=True)
    media_type = models.CharField(max_length=10, default='movie')  # 'movie' or 'tv'
    title = models.CharField(max_length=255)
    data = models.JSONField(null=True, blank=True)  # Cache for TMDB data

    def __str__(self):
        return self.title

class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 11)])
    created_at = models.DateTimeField(default=timezone.now)
    watched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tmdb_api_key = models.CharField(max_length=100, blank=True, verbose_name="TMDB API Key")
    trakt_username = models.CharField(max_length=50, blank=True, verbose_name="Trakt.tv Username")
    trakt_client_id = models.CharField(max_length=100, blank=True, verbose_name="Trakt.tv Client ID")
    plex_webhook_token = models.CharField(max_length=64, blank=True, unique=True, null=True, verbose_name="Plex Webhook Token")
    plex_webhook_enabled = models.BooleanField(default=False, verbose_name="Plex Webhook Enabled")
    plex_webhook_created_at = models.DateTimeField(null=True, blank=True, verbose_name="Plex Webhook Created")
    language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('ru', 'Русский')],
        default='en',
        verbose_name="Interface Language"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user.username}"

    def tmdb_api_key_masked(self):
        if self.tmdb_api_key:
            return f"{self.tmdb_api_key[:4]}...{self.tmdb_api_key[-4:]}"
        return ""

    def trakt_client_id_masked(self):
        if self.trakt_client_id:
            return f"{self.trakt_client_id[:4]}...{self.trakt_client_id[-4:]}"
        return ""
    
    def plex_webhook_token_masked(self):
        if self.plex_webhook_token:
            return f"{self.plex_webhook_token[:8]}...{self.plex_webhook_token[-8:]}"
        return ""

class ImportTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('running', 'Выполняется'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)
    total_items = models.IntegerField(default=0)
    imported_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Import for {self.user.username} - {self.status}"

class PlexWebhookEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, verbose_name="Event Type")
    payload = models.JSONField(verbose_name="Payload")
    processed = models.BooleanField(default=False, verbose_name="Processed")
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Plex Webhook Event"
        verbose_name_plural = "Plex Webhook Events"

    def __str__(self):
        return f"{self.user.username} - {self.event_type} - {self.created_at}"
