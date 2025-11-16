from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, 
    EBike, 
    Booking, 
    VehicleRegistration, 
    ProviderDocument, 
    Favorite, 
    Review, 
    Notification, 
    ContactMessage,
    Withdrawal
)

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_rider', 'is_vehicle_provider', 'is_verified_provider')
    list_filter = ('is_staff', 'is_superuser', 'is_rider', 'is_vehicle_provider', 'is_active')
    search_fields = ('username', 'email', 'mobile_number', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('mobile_number', 'profile_image', 'is_rider', 'is_vehicle_provider', 'is_verified_provider', 'verification_notes')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('mobile_number', 'is_rider', 'is_vehicle_provider'),
            'classes': ('collapse',)
        }),
    )

class EBikeAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'price_per_day', 'price_per_week', 'is_available')
    list_filter = ('is_available', 'provider')
    search_fields = ('name', 'description', 'provider__username')

class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider', 'ebike', 'start_date', 'end_date', 'status', 'total_price', 'is_paid')
    list_filter = ('status', 'is_paid', 'start_date', 'end_date')
    search_fields = ('rider__username', 'ebike__name', 'id')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('rider', 'ebike')

class VehicleRegistrationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'vehicle_number', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('provider__username', 'vehicle_number')
    list_select_related = ('provider',)

class ProviderDocumentAdmin(admin.ModelAdmin):
    list_display = ('provider', 'document_type', 'status', 'uploaded_at')
    list_filter = ('document_type', 'status')
    search_fields = ('provider__username', 'document_number')
    readonly_fields = ('uploaded_at', 'reviewed_at')
    list_select_related = ('provider', 'reviewed_by')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'ebike', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('name', 'message', 'user__username', 'ebike__name')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'ebike')
    
    def save_model(self, request, obj, form, change):
        if obj.user and not obj.name:
            obj.name = obj.user.username
        super().save_model(request, obj, form, change)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message_preview', 'is_read', 'created_at', 'is_public')
    list_filter = ('is_read', 'is_public')
    search_fields = ('recipient__username', 'message')
    readonly_fields = ('created_at',)
    list_select_related = ('recipient',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'responded', 'created_at')
    list_filter = ('responded', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    actions = ['mark_as_responded']

    def mark_as_responded(self, request, queryset):
        updated = queryset.update(responded=True)
        self.message_user(request, f"Marked {updated} message(s) as responded.")
    mark_as_responded.short_description = 'Mark selected as responded'

class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'amount', 'status', 'account_holder_name', 'created_at', 'processed_at')
    list_filter = ('status', 'created_at', 'processed_at')
    search_fields = ('provider__username', 'account_holder_name', 'account_number', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'processed_at', 'processed_by')
    list_select_related = ('provider', 'processed_by')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Withdrawal Details', {
            'fields': ('provider', 'amount', 'status')
        }),
        ('Account Information', {
            'fields': ('account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id')
        }),
        ('Processing Information', {
            'fields': ('processed_by', 'processed_at', 'transaction_id', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Register all models
admin.site.register(User, UserAdmin)
admin.site.register(EBike, EBikeAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(VehicleRegistration, VehicleRegistrationAdmin)
admin.site.register(ProviderDocument, ProviderDocumentAdmin)
admin.site.register(Favorite)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(Withdrawal, WithdrawalAdmin)
