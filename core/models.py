from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

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
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    ebike = models.ForeignKey(EBike, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField(help_text="Format: YYYY-MM-DD")
    end_date = models.DateField(help_text="Format: YYYY-MM-DD")
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError
        from datetime import date
        
        # Convert string dates to date objects if needed
        if isinstance(self.start_date, str):
            try:
                from django.utils.dateparse import parse_date
                self.start_date = parse_date(self.start_date)
            except (ValueError, TypeError):
                raise ValidationError({
                    'start_date': 'Enter a valid date in YYYY-MM-DD format.'
                })
                
        if isinstance(self.end_date, str):
            try:
                from django.utils.dateparse import parse_date
                self.end_date = parse_date(self.end_date)
            except (ValueError, TypeError):
                raise ValidationError({
                    'end_date': 'Enter a valid date in YYYY-MM-DD format.'
                })
        
        # Ensure dates are valid date objects
        if not isinstance(self.start_date, date) or not isinstance(self.end_date, date):
            raise ValidationError('Invalid date format. Please use YYYY-MM-DD.')
        
        # Ensure end_date is after start_date
        if self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'End date must be after start date.'
            })
            
        # Ensure dates are not in the past
        if self.start_date < date.today():
            raise ValidationError({
                'start_date': 'Start date cannot be in the past.'
            })
            
        # Call parent's clean method
        super().clean()

    def save(self, *args, **kwargs):
        # Convert string dates to date objects if needed
        if isinstance(self.start_date, str):
            from django.utils.dateparse import parse_date
            self.start_date = parse_date(self.start_date) or self.start_date
            
        if isinstance(self.end_date, str):
            from django.utils.dateparse import parse_date
            self.end_date = parse_date(self.end_date) or self.end_date
        
        # Run full validation before saving
        self.full_clean()
        
        # Set timestamps if not set
        if not self.id and not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        
        # Maintain backward compatibility with is_approved and is_rejected
        if self.status == 'approved':
            self.is_approved = True
            self.is_rejected = False
        elif self.status == 'rejected':
            self.is_approved = False
            self.is_rejected = True
        else:
            self.is_approved = False
            self.is_rejected = False
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rider.username}'s booking for {self.ebike.name} ({self.get_status_display()})"

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    name = models.CharField(max_length=100, blank=True, null=True)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False, help_text="Should this review be shown on the website?")

    def save(self, *args, **kwargs):
        # If user is authenticated and name is not provided, use user's username
        if self.user and not self.name:
            self.name = self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review by {self.name or 'Anonymous'} - {self.rating} stars"


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
