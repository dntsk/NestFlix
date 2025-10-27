from django.core.management.base import BaseCommand
from catalog.poster_cache import cleanup_orphaned_posters


class Command(BaseCommand):
    help = 'Remove orphaned poster files that are no longer referenced in database'

    def handle(self, *args, **options):
        self.stdout.write('Starting poster cleanup...')
        
        removed_count = cleanup_orphaned_posters()
        
        if removed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Removed {removed_count} orphaned poster files')
            )
        else:
            self.stdout.write('No orphaned posters found')
