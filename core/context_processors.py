from django.apps import apps

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