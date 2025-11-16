"""
Models for the core application of the AisEbikeRental system.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """
    Extended User model for the e-bike rental system.

    Inherits from Django's AbstractUser and adds fields for user roles,
    contact information, and provider verification status.
    """
    is_rider = models.BooleanField(default=False)
    is_vehicle_provider = models.BooleanField(default=False)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_verified_provider = models.BooleanField(default=False, help_text="Admin verification status for vehicle providers")
    verification_notes = models.TextField(blank=True, null=True, help_text="Admin notes about verification")


class EBike(models.Model):
    """
    Model representing an electric bike available for rental.

    Contains details about the e-bike such as name, description,
    pricing, and availability status.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_week = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='ebikes/')
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ebikes')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.provider.username}"


class Booking(models.Model):
    """
    Model for booking e-bike rentals.

    Handles the reservation process including dates, pricing,
    payment tracking, and approval status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    ebike = models.ForeignKey(EBike, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField(help_text="Format: YYYY-MM-DD")
    start_time = models.TimeField(default="09:00", help_text="Pickup time")
    end_date = models.DateField(help_text="Format: YYYY-MM-DD")
    end_time = models.TimeField(default="18:00", help_text="Return time")
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
            
        # Ensure dates are not in the past for new or modified bookings
        is_new_booking = self.pk is None
        start_date_changed = False
        if not is_new_booking and self.pk:
            original = self.__class__.objects.filter(pk=self.pk).values('start_date').first()
            if original:
                start_date_changed = original['start_date'] != self.start_date
        if self.start_date < date.today() and (is_new_booking or start_date_changed):
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

    @property
    def days(self):
        """Calculate the number of days for the booking."""
        if self.start_date and self.end_date:
            start = self.start_date
            end = self.end_date

            # Handle date objects
            if hasattr(start, 'days'):  # timedelta
                pass
            else:
                from datetime import date
                from django.utils.dateparse import parse_date
                if isinstance(start, str):
                    start = parse_date(start)
                if isinstance(end, str):
                    end = parse_date(end)

                if isinstance(start, date) and isinstance(end, date):
                    return (end - start).days

        return 0



    def __str__(self):
        return f"{self.rider.username}'s booking for {self.ebike.name} ({self.get_status_display()})"


class VehicleRegistration(models.Model):
    """
    Model for vehicle registrations submitted by providers.

    Tracks document submissions for legal vehicle registration
    and approval status by administrators.
    """
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_registrations')
    vehicle_number = models.CharField(max_length=20)
    rc_document = models.FileField(upload_to='rc_documents/')
    is_approved = models.BooleanField(default=False)


class ProviderDocument(models.Model):
    """
    Model for documents uploaded by vehicle providers for verification.

    Supports various document types required for provider verification,
    with admin review process and status tracking.
    """
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


class Favorite(models.Model):
    """
    Model for users to save their favorite e-bikes.

    Allows users to create wishlist of e-bikes for easy access later.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    ebike = models.ForeignKey(EBike, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'ebike']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} likes {self.ebike.name}"


class Review(models.Model):
    """
    Model for user reviews and ratings of e-bikes or general feedback.

    Supports both specific e-bike reviews and general website reviews.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    ebike = models.ForeignKey(EBike, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True, help_text="Review for a specific e-bike (optional)")
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
    """
    Model for in-app notifications sent to users.

    Supports both personal notifications to specific users and
    public announcements visible to all users.
    """
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
    """
    Model for contact form submissions.

    Allows users to send inquiries or messages to the website administrators.
    """
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


class Withdrawal(models.Model):
    """
    Model for withdrawal requests from providers.

    Handles payment withdrawals from provider earnings to bank accounts or UPI,
    with admin approval and processing tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount to withdraw")
    account_number = models.CharField(max_length=50, help_text="Bank account number or UPI ID")
    account_holder_name = models.CharField(max_length=100, help_text="Account holder name")
    ifsc_code = models.CharField(max_length=20, blank=True, null=True, help_text="IFSC code (for bank transfers)")
    bank_name = models.CharField(max_length=100, blank=True, null=True, help_text="Bank name")
    upi_id = models.CharField(max_length=100, blank=True, null=True, help_text="UPI ID (alternative to bank transfer)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes about the withdrawal")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdrawals')
    processed_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="Transaction ID after transfer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Withdrawal #{self.id} - {self.provider.username} - ₹{self.amount} ({self.get_status_display()})"
