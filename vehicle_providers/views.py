from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import EBike, Booking, VehicleRegistration, ProviderDocument
from .forms import EBikeForm, VehicleRegistrationForm, ProviderDocumentForm
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
    # Check if provider is verified
    if not request.user.is_verified_provider:
        messages.error(request, 'You must be a verified provider to add ebikes. Please upload and get your documents verified first.')
        return redirect('upload_documents')
    
    if request.method == 'POST':
        form = EBikeForm(request.POST, request.FILES)
        if form.is_valid():
            ebike = form.save(commit=False)
            ebike.provider = request.user
            ebike.save()
            messages.success(request, 'EBike added successfully!')
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
            messages.success(request, 'Vehicle registration submitted successfully!')
            return redirect('vehicle_provider_dashboard')
    else:
        form = VehicleRegistrationForm()
    return render(request, 'vehicle_providers/register_vehicle.html', {'form': form})


@login_required
def upload_documents(request):
    if request.method == 'POST':
        form = ProviderDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.provider = request.user
            document.save()
            messages.success(request, 'Document uploaded successfully! It will be reviewed by admin.')
            return redirect('view_documents')
    else:
        form = ProviderDocumentForm()
    
    return render(request, 'vehicle_providers/upload_documents.html', {'form': form})


@login_required
def view_documents(request):
    documents = ProviderDocument.objects.filter(provider=request.user)
    verification_status = request.user.is_verified_provider
    
    return render(request, 'vehicle_providers/view_documents.html', {
        'documents': documents,
        'verification_status': verification_status,
    })

