from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from core.models import Booking, EBike


def _recompute_bike_availability(bike: EBike):
    today = timezone.localdate()
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
        bike.save(update_fields=["is_available"])  # minimal write


@receiver(post_save, sender=Booking)
def update_bike_availability_on_booking_save(sender, instance: Booking, **kwargs):
    _recompute_bike_availability(instance.ebike)


@receiver(post_delete, sender=Booking)
def update_bike_availability_on_booking_delete(sender, instance: Booking, **kwargs):
    _recompute_bike_availability(instance.ebike)
