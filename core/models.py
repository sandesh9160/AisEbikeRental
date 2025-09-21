from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_rider = models.BooleanField(default=False)
    is_vehicle_provider = models.BooleanField(default=False)
    mobile_number = models.CharField(max_length=15)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_verified_provider = models.BooleanField(default=False, help_text="Admin verification status for vehicle providers")
    verification_notes = models.TextField(blank=True, null=True, help_text="Admin notes about verification")

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
    is_rejected = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

class VehicleRegistration(models.Model):
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_registrations')
    vehicle_number = models.CharField(max_length=20)
    rc_document = models.FileField(upload_to='rc_documents/')
    is_approved = models.BooleanField(default=False)


class ProviderDocument(models.Model):
    DOCUMENT_TYPES = [
        ('aadhar', 'Aadhar Card'),
        ('pan', 'PAN Card'),
        ('driving_license', 'Driving License'),
        ('business_license', 'Business License'),
        ('insurance', 'Insurance Document'),
        ('other', 'Other'),
    ]
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='provider_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='provider_documents/')
    document_number = models.CharField(max_length=100, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes about this document")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_documents')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.provider.username} - {self.get_document_type_display()}"


class Review(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)
    is_public = models.BooleanField(default=False, help_text="Show to all users, including guests.")

    def __str__(self):
        if self.is_public:
            return f"Public: {self.message[:30]}..."
        return f"To {self.recipient.username if self.recipient else 'Public'}: {self.message[:30]}..."


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} from {self.name}"


