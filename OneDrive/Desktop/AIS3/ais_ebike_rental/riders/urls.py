from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.rider_dashboard, name='rider_dashboard'),
    path('book/<int:ebike_id>/', views.book_ebike, name='book_ebike'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('payment/<int:booking_id>/', views.payment, name='payment'),
    path('download-receipt/<int:booking_id>/', views.download_receipt, name='download_receipt'),
    path('mark-notification-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
]

