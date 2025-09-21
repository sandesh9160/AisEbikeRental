from django.contrib import admin
from .models import User, EBike, Booking, VehicleRegistration, ContactMessage, Review

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_rider', 'is_vehicle_provider', 'mobile_number')
    search_fields = ('username', 'email', 'mobile_number')

admin.site.register(User, UserAdmin)
admin.site.register(EBike)
admin.site.register(Booking)
admin.site.register(VehicleRegistration)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'responded', 'created_at')
    list_filter = ('responded', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    ordering = ('-created_at',)

    actions = ['mark_as_responded']

    def mark_as_responded(self, request, queryset):
        updated = queryset.update(responded=True)
        self.message_user(request, f"Marked {updated} message(s) as responded.")
    mark_as_responded.short_description = 'Mark selected as responded'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('name', 'message')
