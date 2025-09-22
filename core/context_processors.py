from django.apps import apps
from django.core.cache import cache

def unread_notification_count(request):
    try:
        Notification = apps.get_model('core', 'Notification')
        public_count = Notification.objects.filter(is_public=True).count()
        if request.user.is_authenticated:
            user_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            count = public_count + user_count
        else:
            count = public_count
    except Exception:
        count = 0
    return {'unread_notification_count': count} 


def availability_sync_info(request):
    """Expose the last availability sync date (if any) to all templates."""
    try:
        last_sync = cache.get("bike_availability_last_sync_date")
    except Exception:
        last_sync = None
    return {"availability_last_sync_date": last_sync}