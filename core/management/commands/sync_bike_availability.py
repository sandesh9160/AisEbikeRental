from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone

from core.utils import sync_bike_availability


class Command(BaseCommand):
    help = "Sync EBike.is_available based on current date and approved, non-rejected bookings."

    def handle(self, *args, **options):
        updated = sync_bike_availability()
        # Update last sync date in cache for dashboard visibility
        today = timezone.localdate().isoformat()
        cache.set("bike_availability_last_sync_date", today, timeout=24 * 60 * 60)
        self.stdout.write(self.style.SUCCESS(f"Sync complete. Bikes updated: {updated}"))
