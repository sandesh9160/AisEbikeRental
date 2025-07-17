from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.rider_dashboard, name='rider_dashboard'),
    path('book/<int:ebike_id>/', views.book_ebike, name='book_ebike'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
]

