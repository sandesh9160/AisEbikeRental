from django.core.management.base import BaseCommand
<<<<<<< HEAD
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
=======
from django.utils import timezone
from datetime import datetime, date
from core.models import Booking, EBike


class Command(BaseCommand):
    help = 'Update e-bike availability based on booking end times'

    def handle(self, *args, **options):
        now = timezone.now()

        # Get all approved bookings
        expired_bookings = Booking.objects.filter(
            status='approved',
            ebike__is_available=False
        ).select_related('ebike')

        updated_count = 0
        for booking in expired_bookings:
            # Combine date and time to create datetime objects
            try:
                if booking.end_date and booking.end_time:
                    # Check if booking has ended
                    end_datetime = datetime.combine(
                        booking.end_date,
                        booking.end_time
                    )
                    end_datetime = timezone.make_aware(end_datetime)

                    if now > end_datetime:
                        # Booking has ended, make e-bike available
                        booking.ebike.is_available = True
                        booking.ebike.save(update_fields=['is_available'])
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Made e-bike "{booking.ebike.name}" (ID: {booking.ebike.id}) available - '
                                f'Booking #{booking.id} ended at {end_datetime}'
                            )
                        )
            except (AttributeError, TypeError, ValueError) as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Could not process booking #{booking.id}: {e}'
                    )
                )

        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} e-bikes to available status')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No e-bikes needed to be updated')
            )
>>>>>>> bc478c3b2f51a242be15138610bac84cb0a5f46a
