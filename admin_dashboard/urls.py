from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('approve-booking/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    path('approve-vehicle-registration/<int:registration_id>/', views.approve_vehicle_registration, name='approve_vehicle_registration'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]

