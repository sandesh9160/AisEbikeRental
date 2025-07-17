from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.vehicle_provider_dashboard, name='vehicle_provider_dashboard'),
    path('add-ebike/', views.add_ebike, name='add_ebike'),
    path('register-vehicle/', views.register_vehicle, name='register_vehicle'),
]

