from django.contrib import admin
from .models import User, EBike, Booking, VehicleRegistration

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_rider', 'is_vehicle_provider', 'mobile_number')
    search_fields = ('username', 'email', 'mobile_number')

admin.site.register(User, UserAdmin)
admin.site.register(EBike)
admin.site.register(Booking)
admin.site.register(VehicleRegistration)
