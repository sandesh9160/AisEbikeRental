from django.core.management.base import BaseCommand
from core.utils import sync_bike_availability


class Command(BaseCommand):
    help = 'Update e-bike availability in real-time based on current booking status and expiry times'

    def add_arguments(self, parser):
        parser.add_argument(
            '--silent',
            action='store_true',
            help='Run silently without stdout messages (useful for cron jobs)',
        )

    def handle(self, *args, **options):
        silent = options.get('silent', False)

        if not silent:
            self.stdout.write('Starting real-time bike availability sync...')

        # Use the improved sync function that handles both date AND time
        updated_count = sync_bike_availability()

        if updated_count > 0:
            message = f'Successfully updated {updated_count} e-bike(s) availability status'
            if silent:
                self.stderr.write(message)  # Use stderr for cron job logs
            else:
                self.stdout.write(self.style.SUCCESS(message))
        else:
            message = 'No e-bikes needed availability status updates'
            if silent:
                # Don't output anything if silent and nothing changed
                pass
            else:
                self.stdout.write(message)

        if not silent:
            self.stdout.write('Bike availability sync completed.')
