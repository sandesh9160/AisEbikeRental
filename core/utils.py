from django.utils import timezone
from django.db import transaction

from core.models import EBike, Booking


def sync_bike_availability() -> int:
    """Recompute EBike.is_available based on today's date and bookings.

    Returns the number of bikes whose availability was updated.
    """
    today = timezone.localdate()
    updated = 0
    with transaction.atomic():
        for bike in EBike.objects.all():
            has_active_booking = Booking.objects.filter(
                ebike=bike,
                is_approved=True,
                is_rejected=False,
                is_paid=True,
                start_date__lte=today,
                end_date__gte=today,
            ).exists()
            new_available = not has_active_booking
            if bike.is_available != new_available:
                bike.is_available = new_available
                bike.save(update_fields=["is_available"]) 
                updated += 1
    return updated
