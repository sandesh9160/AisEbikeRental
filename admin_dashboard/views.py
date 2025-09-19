from django.shortcuts import render, redirect,get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from core.models import User, EBike, Booking, VehicleRegistration, Notification, ProviderDocument
from django.db.models import Sum
from decimal import Decimal
from django.db.models.functions import TruncMonth
from django.db.models import Count
import json

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
        bikes = []

        for bike in provider.ebikes.all():
            earnings = Booking.objects.filter(ebike=bike, is_approved=True).aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.0')
            total_earnings += earnings
            bikes.append(bike)

        # Calculate platform charges for the provider
        platform_charges = total_earnings * platform_charge_percentage
        total_platform_charges += platform_charges
        total_providers_earnings += total_earnings

        providers_earnings.append({
            'username': provider.username,
            'bikes': bikes,
            'total_earnings': total_earnings,
        })

    # Bookings per month for the last 12 months
    bookings_by_month = (
        Booking.objects
        .annotate(month=TruncMonth('start_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    months = [b['month'].strftime('%b %Y') for b in bookings_by_month]
    counts = [b['count'] for b in bookings_by_month]

    approved_count = Booking.objects.filter(is_approved=True).count()
    pending_count = Booking.objects.filter(is_approved=False).count()
    pending_approvals_count = Booking.objects.filter(is_approved=False).count()

    unread_notification_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    
    # Document verification data
    pending_documents = ProviderDocument.objects.filter(status='pending').order_by('-uploaded_at')
    pending_providers = User.objects.filter(is_vehicle_provider=True, is_verified_provider=False)
    
    return render(request, 'admin_dashboard/dashboard.html', {
        'riders': riders,
        'vehicle_providers': vehicle_providers,
        'ebikes': ebikes,
        'bookings': bookings,
        'providers_earnings': providers_earnings,
        'total_providers_earnings': total_providers_earnings,
        'platform_charges': total_platform_charges,
        'unread_notification_count': unread_notification_count,
        'notifications': notifications,
        'chart_months': json.dumps(months),
        'chart_counts': json.dumps(counts),
        'approved_count': approved_count,
        'pending_count': pending_count,
        'pending_approvals_count': pending_approvals_count,
        'pending_documents': pending_documents,
        'pending_providers': pending_providers,
    })


@user_passes_test(is_admin)
def approve_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    booking.is_approved = True
    booking.save()
    # Notify the user
    Notification.objects.create(
        recipient=booking.rider,
        message=f"Your booking for {booking.ebike.name} has been approved!",
        link=f"/riders/booking/confirmation/{booking.id}/"
    )
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
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.delete()
    return redirect(request.GET.get('next') or reverse('admin_dashboard'))

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.delete()
    return redirect('admin_dashboard')


@user_passes_test(is_admin)
def review_documents(request):
    pending_documents = ProviderDocument.objects.filter(status='pending').order_by('-uploaded_at')
    approved_documents = ProviderDocument.objects.filter(status='approved').order_by('-reviewed_at')
    rejected_documents = ProviderDocument.objects.filter(status='rejected').order_by('-reviewed_at')
    
    return render(request, 'admin_dashboard/review_documents.html', {
        'pending_documents': pending_documents,
        'approved_documents': approved_documents,
        'rejected_documents': rejected_documents,
    })


@user_passes_test(is_admin)
def verify_document(request, document_id):
    if request.method == 'POST':
        document = get_object_or_404(ProviderDocument, id=document_id)
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            document.status = 'approved'
            document.admin_notes = admin_notes
            document.reviewed_by = request.user
            document.reviewed_at = timezone.now()
            document.save()
            
            # Check if all documents are approved to verify the provider
            all_documents = ProviderDocument.objects.filter(provider=document.provider)
            if all_documents.filter(status='pending').count() == 0:
                document.provider.is_verified_provider = True
                document.provider.verification_notes = f"Verified on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                document.provider.save()
                
                # Notify provider
                Notification.objects.create(
                    recipient=document.provider,
                    message="Congratulations! Your account has been verified. You can now add ebikes to the platform.",
                    link="/vehicle-providers/dashboard/"
                )
                messages.success(request, f'Document approved and provider {document.provider.username} has been verified!')
            else:
                messages.success(request, 'Document approved successfully!')
                
        elif action == 'reject':
            document.status = 'rejected'
            document.admin_notes = admin_notes
            document.reviewed_by = request.user
            document.reviewed_at = timezone.now()
            document.save()
            
            # Notify provider
            Notification.objects.create(
                recipient=document.provider,
                message=f"Your document {document.get_document_type_display()} was rejected. Please review the admin notes and resubmit.",
                link="/vehicle-providers/view-documents/"
            )
            messages.success(request, 'Document rejected successfully!')
        
        return redirect('review_documents')
    
    document = get_object_or_404(ProviderDocument, id=document_id)
    return render(request, 'admin_dashboard/verify_document.html', {'document': document})


@user_passes_test(is_admin)
def verify_provider(request, provider_id):
    provider = get_object_or_404(User, id=provider_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        verification_notes = request.POST.get('verification_notes', '')
        
        if action == 'verify':
            provider.is_verified_provider = True
            provider.verification_notes = verification_notes
            provider.save()
            
            # Notify provider
            Notification.objects.create(
                recipient=provider,
                message="Congratulations! Your account has been verified. You can now add ebikes to the platform.",
                link="/vehicle-providers/dashboard/"
            )
            messages.success(request, f'Provider {provider.username} has been verified successfully!')
            
        elif action == 'reject':
            provider.is_verified_provider = False
            provider.verification_notes = verification_notes
            provider.save()
            
            # Notify provider
            Notification.objects.create(
                recipient=provider,
                message="Your account verification was rejected. Please review the admin notes and contact support.",
                link="/vehicle-providers/view-documents/"
            )
            messages.success(request, f'Provider {provider.username} verification rejected!')
        
        return redirect('admin_dashboard')
    
    provider_documents = ProviderDocument.objects.filter(provider=provider)
    return render(request, 'admin_dashboard/verify_provider.html', {
        'provider': provider,
        'provider_documents': provider_documents,
    })

