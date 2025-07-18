from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import EBike, Booking, VehicleRegistration
from .forms import EBikeForm, VehicleRegistrationForm
from decimal import Decimal

@login_required
def vehicle_provider_dashboard(request):
    ebikes = EBike.objects.filter(provider=request.user)
    bookings = Booking.objects.filter(ebike__provider=request.user)
    total_earnings = sum(float(booking.total_price) for booking in bookings if booking.is_approved)
    platform_charges = total_earnings * 0.1
    return render(request, 'vehicle_providers/dashboard.html', {
        'ebikes': ebikes,
        'bookings': bookings,
        'total_earnings': total_earnings,
        'platform_charges': platform_charges
    })


@login_required
def add_ebike(request):
    if request.method == 'POST':
        form = EBikeForm(request.POST, request.FILES)
        if form.is_valid():
            ebike = form.save(commit=False)
            ebike.provider = request.user
            ebike.save()
            return redirect('vehicle_provider_dashboard')
    else:
        form = EBikeForm()
    return render(request, 'vehicle_providers/add_ebike.html', {'form': form})

@login_required
def register_vehicle(request):
    if request.method == 'POST':
        form = VehicleRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.provider = request.user
            registration.save()
            return redirect('vehicle_provider_dashboard')
    else:
        form = VehicleRegistrationForm()
    return render(request, 'vehicle_providers/register_vehicle.html', {'form': form})

