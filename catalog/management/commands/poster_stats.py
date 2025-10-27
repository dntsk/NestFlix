from django.core.management.base import BaseCommand
from catalog.models import Movie
from django.db.models import Q


class Command(BaseCommand):
    help = 'Show poster cache statistics'

    def handle(self, *args, **options):
        total_movies = Movie.objects.filter(data__isnull=False).count()
        cached_posters = Movie.objects.filter(
            poster_file__isnull=False
        ).exclude(poster_file='').count()
        
        movies_needing_refresh = Movie.objects.filter(
            data__isnull=False
        ).filter(
            Q(poster_file='') | Q(poster_cached_at__isnull=True)
        ).count()
        
        cache_percentage = (cached_posters / total_movies * 100) if total_movies > 0 else 0
        
        self.stdout.write('\n=== Poster Cache Statistics ===')
        self.stdout.write(f'Total movies with data: {total_movies}')
        self.stdout.write(f'Cached posters: {cached_posters}')
        self.stdout.write(f'Movies needing cache: {movies_needing_refresh}')
        self.stdout.write(f'Cache coverage: {cache_percentage:.1f}%')
        self.stdout.write('=' * 31 + '\n')
