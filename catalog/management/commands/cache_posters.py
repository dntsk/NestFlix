from django.core.management.base import BaseCommand
from django.db.models import Q
from catalog.models import Movie
from catalog.poster_cache import download_tmdb_poster
from catalog.logger import logger


class Command(BaseCommand):
    help = 'Cache movie posters locally from TMDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Cache all posters (including expired)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of posters to cache',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-download even if cached',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting poster caching...'))
        
        if options['all']:
            movies = Movie.objects.filter(data__isnull=False)
        elif options['force']:
            movies = Movie.objects.filter(data__isnull=False)
        else:
            movies = Movie.objects.filter(
                Q(poster_file='') | Q(poster_file__isnull=True),
                data__isnull=False
            )
        
        if options['limit']:
            movies = movies[:options['limit']]
        
        total = movies.count()
        self.stdout.write(f'Found {total} movies to process')
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, movie in enumerate(movies, 1):
            if not options['force'] and movie.poster_file and not movie.needs_poster_refresh():
                self.stdout.write(f'[{i}/{total}] Skipping {movie.title} (already cached)')
                skipped_count += 1
                continue
            
            self.stdout.write(f'[{i}/{total}] Caching poster for: {movie.title}')
            
            try:
                success = download_tmdb_poster(movie)
                
                if success:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Successfully cached poster')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ✗ Failed to cache poster')
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error: {str(e)}')
                )
                logger.error(f'Error caching poster for {movie.title}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {success_count} cached, {error_count} errors, {skipped_count} skipped'
            )
        )
