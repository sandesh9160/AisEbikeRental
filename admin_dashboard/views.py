from django.shortcuts import render, redirect,get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import user_passes_test
from core.models import User, EBike, Booking, VehicleRegistration
from django.db.models import Sum
from decimal import Decimal

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    riders = User.objects.filter(is_rider=True)
    vehicle_providers = User.objects.filter(is_vehicle_provider=True)
    ebikes = EBike.objects.all()
    bookings = Booking.objects.all()

    # Assume platform charges are 10% of each provider's earnings
    platform_charge_percentage = Decimal('0.10')

    providers_earnings = []
    total_platform_charges = Decimal('0.0')  # Variable to store total platform charges
    total_providers_earnings = Decimal('0.0')

    for provider in vehicle_providers:
        total_earnings = Decimal('0.0')
        bike_names = []

        for bike in provider.ebikes.all():
            earnings = Booking.objects.filter(ebike=bike, is_approved=True).aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.0')
            total_earnings += earnings
            bike_names.append(bike.name)

        # Calculate platform charges for the provider
        platform_charges = total_earnings * platform_charge_percentage
        total_platform_charges += platform_charges
        total_providers_earnings += total_earnings

        providers_earnings.append({
            'username': provider.username,
            'bike_names': ", ".join(bike_names),
            'total_earnings': total_earnings,
        })

    return render(request, 'admin_dashboard/dashboard.html', {
        'riders': riders,
        'vehicle_providers': vehicle_providers,
        'ebikes': ebikes,
        'bookings': bookings,
        'providers_earnings': providers_earnings,
        'total_providers_earnings': total_providers_earnings,
        'platform_charges': total_platform_charges,  # Send total platform charges to the template
    })


@user_passes_test(is_admin)
def approve_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    booking.is_approved = True
    booking.save()
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def approve_vehicle_registration(request, registration_id):
    registration = VehicleRegistration.objects.get(id=registration_id)
    registration.is_approved = True
    registration.save()
    return redirect('admin_dashboard')

@user_passes_test(is_admin, login_url='login')
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.is_approved = False
    booking.is_rejected = True
    booking.save()
    return redirect(request.GET.get('next') or reverse('admin_dashboard'))

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.delete()
    return redirect('admin_dashboard')

