from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_rider = models.BooleanField(default=False)
    is_vehicle_provider = models.BooleanField(default=False)
    mobile_number = models.CharField(max_length=15)

class EBike(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_week = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='ebikes/')
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ebikes')
    is_available = models.BooleanField(default=True)

class Booking(models.Model):
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    ebike = models.ForeignKey(EBike, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_approved = models.BooleanField(default=False)

class VehicleRegistration(models.Model):
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_registrations')
    vehicle_number = models.CharField(max_length=20)
    rc_document = models.FileField(upload_to='rc_documents/')
    is_approved = models.BooleanField(default=False)

