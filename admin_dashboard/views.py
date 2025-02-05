from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from core.models import User, EBike, Booking, VehicleRegistration
from django.db.models import Sum,Q

def is_admin(user):
    return user.is_authenticated and user.is_staff

# Define the custom permission check (assuming is_admin function is implemented)

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Retrieve all riders, vehicle providers, e-bikes, and bookings
    riders = User.objects.filter(is_rider=True)
    vehicle_providers = User.objects.filter(is_vehicle_provider=True)
    ebikes = EBike.objects.all()
    bookings = Booking.objects.all()

    # Aggregate total earnings and bike name for each vehicle provider
    providers_earnings = []
    
    for provider in vehicle_providers:
        total_earnings = 0
        bike_names = []
        
        # Iterate through the bikes of the vehicle provider
        for bike in provider.ebikes.all():
            # Calculate total earnings for each bike
            total_earnings += Booking.objects.filter(ebike=bike, is_approved=True).aggregate(Sum('total_price'))['total_price__sum'] or 0
            bike_names.append(bike.name)
        
        providers_earnings.append({
            'username': provider.username,
            'bike_names': ", ".join(bike_names),  # Join bike names if multiple
            'total_earnings': total_earnings
        })

    # Calculate the total earnings for all providers
    total_providers_earnings = sum(provider['total_earnings'] for provider in providers_earnings)

    # Render the admin dashboard template
    return render(request, 'admin_dashboard/dashboard.html', {
        'riders': riders,
        'vehicle_providers': vehicle_providers,
        'ebikes': ebikes,
        'bookings': bookings,
        'providers_earnings': providers_earnings,
        'total_providers_earnings': total_providers_earnings,
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

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.delete()
    return redirect('admin_dashboard')

