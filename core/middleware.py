from django.core.cache import cache
from django.utils import timezone

from core.utils import sync_bike_availability


class DailyAvailabilitySyncMiddleware:
    """Runs a lightweight availability sync once per day on the first incoming request.

    This is a safety net to ensure bikes become available when bookings expire,
    even if no Booking save event occurs that day. For production-grade scheduling,
    also schedule the management command `sync_bike_availability` daily.
    """

    CACHE_KEY = "bike_availability_last_sync_date"
    _LAST_SYNC_DATE = None  # in-process fallback for environments without a real cache

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = timezone.localdate().isoformat()
        last_sync = cache.get(self.CACHE_KEY)
        # If cache backend is DummyCache, use in-process fallback to avoid syncing every request
        effective_last_sync = last_sync or self._LAST_SYNC_DATE
        if effective_last_sync != today:
            # Best-effort: avoid blocking for too long; the operation is lightweight
            sync_bike_availability()
            cache.set(self.CACHE_KEY, today, timeout=24 * 60 * 60)
            DailyAvailabilitySyncMiddleware._LAST_SYNC_DATE = today
        response = self.get_response(request)
        return response
