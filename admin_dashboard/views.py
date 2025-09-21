from django.shortcuts import render, redirect,get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from core.models import User, EBike, Booking, VehicleRegistration, Notification, ProviderDocument, ContactMessage, Review
from django.db.models import Sum, Q
from decimal import Decimal
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Base querysets (no filters here per request)
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
    pending_count = Booking.objects.filter(is_approved=False, is_rejected=False).count()
    pending_approvals_count = Booking.objects.filter(is_approved=False, is_rejected=False).count()

    unread_notification_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    
    # Document verification data
    pending_documents = ProviderDocument.objects.filter(status='pending').order_by('-uploaded_at')
    pending_providers = User.objects.filter(is_vehicle_provider=True, is_verified_provider=False)
    prov_q = request.GET.get('prov_q', '').strip()
    verified_qs = User.objects.filter(is_vehicle_provider=True, is_verified_provider=True)
    unverified_qs = User.objects.filter(is_vehicle_provider=True, is_verified_provider=False)
    if prov_q:
        verified_qs = verified_qs.filter(Q(username__icontains=prov_q) | Q(email__icontains=prov_q))
        unverified_qs = unverified_qs.filter(Q(username__icontains=prov_q) | Q(email__icontains=prov_q))

    vpage = request.GET.get('vpage', 1)
    upage = request.GET.get('upage', 1)
    vp = Paginator(verified_qs.order_by('username'), 10)
    up = Paginator(unverified_qs.order_by('username'), 10)
    verified_page_obj = vp.get_page(vpage)
    unverified_page_obj = up.get_page(upage)
    verified_providers = verified_page_obj.object_list
    unverified_providers = unverified_page_obj.object_list
    # Recent user reviews for dashboard feedback section
    recent_feedback = Review.objects.all()[:10]
    
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
        'verified_providers': verified_providers,
        'unverified_providers': unverified_providers,
        'verified_page_obj': verified_page_obj,
        'unverified_page_obj': unverified_page_obj,
        'prov_q': prov_q,
        'recent_feedback': recent_feedback,
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
    # Filters (applied here as requested)
    provider_id = request.GET.get('provider', '')
    document_type = request.GET.get('document_type', '')
    status = request.GET.get('status', '')  # pending, approved, rejected, or '' for all
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    queryset = ProviderDocument.objects.all()

    if provider_id:
        queryset = queryset.filter(provider_id=provider_id)
    if document_type:
        queryset = queryset.filter(document_type=document_type)
    if status in ['pending', 'approved', 'rejected']:
        queryset = queryset.filter(status=status)
    if date_from:
        try:
            df = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(uploaded_at__date__gte=df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(uploaded_at__date__lte=dt)
        except ValueError:
            pass
    if search:
        queryset = queryset.filter(
            Q(provider__username__icontains=search) |
            Q(document_number__icontains=search)
        )

    # Split by status
    pending_documents = queryset.filter(status='pending').order_by('-uploaded_at')
    approved_documents = queryset.filter(status='approved').order_by('-reviewed_at')
    rejected_documents = queryset.filter(status='rejected').order_by('-reviewed_at')

    # Group by provider
    from collections import defaultdict
    pending_by_provider = defaultdict(list)
    for doc in pending_documents:
        pending_by_provider[doc.provider].append(doc)
    approved_by_provider = defaultdict(list)
    for doc in approved_documents:
        approved_by_provider[doc.provider].append(doc)
    rejected_by_provider = defaultdict(list)
    for doc in rejected_documents:
        rejected_by_provider[doc.provider].append(doc)

    all_providers = User.objects.filter(is_vehicle_provider=True).order_by('username')

    return render(request, 'admin_dashboard/review_documents.html', {
        'pending_documents': pending_documents,
        'approved_documents': approved_documents,
        'rejected_documents': rejected_documents,
        'pending_by_provider': dict(pending_by_provider),
        'approved_by_provider': dict(approved_by_provider),
        'rejected_by_provider': dict(rejected_by_provider),
        # Filters context
        'all_providers': all_providers,
        'current_provider': provider_id,
        'current_document_type': document_type,
        'current_status': status,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'current_search': search,
        'total_documents': queryset.count(),
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


@user_passes_test(is_admin)
def edit_document_verification(request, document_id):
    """Edit verification details for an approved document"""
    document = get_object_or_404(ProviderDocument, id=document_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'update':
            document.admin_notes = admin_notes
            document.save()
            messages.success(request, 'Document verification details updated successfully!')
            return redirect('review_documents')
            
        elif action == 'remove_verification':
            # Remove verification and set back to pending
            document.status = 'pending'
            document.reviewed_by = None
            document.reviewed_at = None
            document.admin_notes = admin_notes
            document.save()
            
            # If this was the last approved document, unverify the provider
            all_documents = ProviderDocument.objects.filter(provider=document.provider)
            if not all_documents.filter(status='approved').exists():
                document.provider.is_verified_provider = False
                document.provider.verification_notes = f"Verification removed on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                document.provider.save()
                
                # Notify provider
                Notification.objects.create(
                    recipient=document.provider,
                    message="Your document verification has been removed. Please resubmit your documents for verification.",
                    link="/vehicle-providers/view-documents/"
                )
                messages.success(request, 'Document verification removed and provider unverified!')
            else:
                messages.success(request, 'Document verification removed successfully!')
            
            return redirect('review_documents')
    
    return render(request, 'admin_dashboard/edit_document_verification.html', {'document': document})


@user_passes_test(is_admin)
def remove_document_verification(request, document_id):
    """Remove verification for an approved document"""
    document = get_object_or_404(ProviderDocument, id=document_id)
    
    if request.method == 'POST':
        # Remove verification and set back to pending
        document.status = 'pending'
        document.reviewed_by = None
        document.reviewed_at = None
        document.admin_notes = ''
        document.save()
        
        # If this was the last approved document, unverify the provider
        all_documents = ProviderDocument.objects.filter(provider=document.provider)
        if not all_documents.filter(status='approved').exists():
            document.provider.is_verified_provider = False
            document.provider.verification_notes = f"Verification removed on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            document.provider.save()
            
            # Notify provider
            Notification.objects.create(
                recipient=document.provider,
                message="Your document verification has been removed. Please resubmit your documents for verification.",
                link="/vehicle-providers/view-documents/"
            )
            messages.success(request, 'Document verification removed and provider unverified!')
        else:
            messages.success(request, 'Document verification removed successfully!')
        
        return redirect('review_documents')
    
    return render(request, 'admin_dashboard/remove_document_verification.html', {'document': document})


@user_passes_test(is_admin)
@require_POST
def bulk_approve_documents(request):
    """Bulk approve provider documents from review_documents page"""
    # Accept either multiple document_ids fields or a single comma-separated selected_ids
    doc_ids = request.POST.getlist('document_ids')
    if not doc_ids:
        selected_ids = request.POST.get('selected_ids', '')
        if selected_ids:
            for chunk in selected_ids.split(','):
                cid = chunk.strip()
                if cid.isdigit():
                    doc_ids.append(cid)
    admin_notes = request.POST.get('admin_notes', '')

    if not doc_ids:
        messages.error(request, 'No documents selected.')
        return redirect('review_documents')

    documents = ProviderDocument.objects.filter(id__in=doc_ids)
    approved_count = 0
    affected_providers = set()

    for document in documents:
        if document.status != 'approved':
            document.status = 'approved'
            document.admin_notes = admin_notes
            document.reviewed_by = request.user
            document.reviewed_at = timezone.now()
            document.save()
            approved_count += 1
            affected_providers.add(document.provider_id)

    # Verify providers who have no pending documents
    for provider_id in affected_providers:
        all_docs = ProviderDocument.objects.filter(provider_id=provider_id)
        if not all_docs.filter(status='pending').exists():
            provider = User.objects.get(id=provider_id)
            if not provider.is_verified_provider:
                provider.is_verified_provider = True
                provider.verification_notes = f"Verified on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                provider.save()
                Notification.objects.create(
                    recipient=provider,
                    message="Congratulations! Your account has been verified. You can now add ebikes to the platform.",
                    link="/vehicle-providers/dashboard/"
                )

    messages.success(request, f'Successfully approved {approved_count} document(s).')
    return redirect('review_documents')


@user_passes_test(is_admin)
@require_POST
def bulk_reject_documents(request):
    """Bulk reject provider documents from review_documents page"""
    doc_ids = request.POST.getlist('document_ids')
    if not doc_ids:
        selected_ids = request.POST.get('selected_ids', '')
        if selected_ids:
            for chunk in selected_ids.split(','):
                cid = chunk.strip()
                if cid.isdigit():
                    doc_ids.append(cid)
    admin_notes = request.POST.get('admin_notes', '')

    if not doc_ids:
        messages.error(request, 'No documents selected.')
        return redirect('review_documents')

    documents = ProviderDocument.objects.filter(id__in=doc_ids)
    rejected_count = 0

    for document in documents:
        if document.status != 'rejected':
            document.status = 'rejected'
            document.admin_notes = admin_notes
            document.reviewed_by = request.user
            document.reviewed_at = timezone.now()
            document.save()
            rejected_count += 1
            Notification.objects.create(
                recipient=document.provider,
                message=f"Your document {document.get_document_type_display()} was rejected. Please review the admin notes and resubmit.",
                link="/vehicle-providers/view-documents/"
            )

    messages.success(request, f'Successfully rejected {rejected_count} document(s).')
    return redirect('review_documents')
@user_passes_test(is_admin)
@require_POST
def bulk_approve_bookings(request):
    """Bulk approve multiple bookings"""
    booking_ids = request.POST.getlist('booking_ids')
    if booking_ids:
        bookings = Booking.objects.filter(id__in=booking_ids, is_approved=False)
        approved_count = 0
        
        for booking in bookings:
            booking.is_approved = True
            booking.is_rejected = False
            booking.save()
            
            # Notify the user
            Notification.objects.create(
                recipient=booking.rider,
                message=f"Your booking for {booking.ebike.name} has been approved!",
                link=f"/riders/booking/confirmation/{booking.id}/"
            )
            approved_count += 1
        
        messages.success(request, f'Successfully approved {approved_count} booking(s)!')
    else:
        messages.error(request, 'No bookings selected for approval.')
    
    return redirect('admin_dashboard')


@user_passes_test(is_admin)
@require_POST
def bulk_reject_bookings(request):
    """Bulk reject multiple bookings"""
    booking_ids = request.POST.getlist('booking_ids')
    rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
    
    if booking_ids:
        bookings = Booking.objects.filter(id__in=booking_ids, is_approved=False)
        rejected_count = 0
        
        for booking in bookings:
            booking.is_rejected = True
            booking.is_approved = False
            booking.save()
            
            # Notify the user
            Notification.objects.create(
                recipient=booking.rider,
                message=f"Your booking for {booking.ebike.name} has been rejected. Reason: {rejection_reason}",
                link=f"/riders/dashboard/"
            )
            rejected_count += 1
        
        messages.success(request, f'Successfully rejected {rejected_count} booking(s)!')
    else:
        messages.error(request, 'No bookings selected for rejection.')
    
    return redirect('admin_dashboard')


@user_passes_test(is_admin)
@require_POST
def bulk_verify_providers(request):
    """Bulk verify multiple providers"""
    provider_ids = request.POST.getlist('provider_ids')
    verification_notes = request.POST.get('verification_notes', 'Bulk verified by admin')
    
    if provider_ids:
        providers = User.objects.filter(id__in=provider_ids, is_vehicle_provider=True, is_verified_provider=False)
        verified_count = 0
        
        for provider in providers:
            provider.is_verified_provider = True
            provider.verification_notes = verification_notes
            provider.save()
            
            # Notify provider
            Notification.objects.create(
                recipient=provider,
                message="Congratulations! Your account has been verified. You can now add ebikes to the platform.",
                link="/vehicle-providers/dashboard/"
            )
            verified_count += 1
        
        messages.success(request, f'Successfully verified {verified_count} provider(s)!')
    else:
        messages.error(request, 'No providers selected for verification.')
    
    return redirect('admin_dashboard')


@user_passes_test(is_admin)
def get_filtered_data(request):
    """AJAX endpoint for filtered data"""
    booking_status = request.GET.get('booking_status', 'all')
    provider_status = request.GET.get('provider_status', 'all')
    date_range = request.GET.get('date_range', 'all')
    search_query = request.GET.get('search', '')
    paid_status = request.GET.get('paid_status', 'all')
    
    # Apply the same filtering logic as in admin_dashboard
    bookings = Booking.objects.all()
    providers = User.objects.filter(is_vehicle_provider=True)
    
    # Apply filters (same logic as in admin_dashboard)
    if booking_status == 'approved':
        bookings = bookings.filter(is_approved=True)
    elif booking_status == 'pending':
        bookings = bookings.filter(is_approved=False, is_rejected=False)
    elif booking_status == 'rejected':
        bookings = bookings.filter(is_rejected=True)
    
    if provider_status == 'verified':
        providers = providers.filter(is_verified_provider=True)
    elif provider_status == 'unverified':
        providers = providers.filter(is_verified_provider=False)
    
    # Date range filter
    if date_range == 'today':
        today = timezone.now().date()
        bookings = bookings.filter(start_date=today)
    elif date_range == 'week':
        week_ago = timezone.now().date() - timedelta(days=7)
        bookings = bookings.filter(start_date__gte=week_ago)
    elif date_range == 'month':
        month_ago = timezone.now().date() - timedelta(days=30)
        bookings = bookings.filter(start_date__gte=month_ago)
    
    # Search filter
    if search_query:
        bookings = bookings.filter(
            Q(rider__username__icontains=search_query) |
            Q(ebike__name__icontains=search_query) |
            Q(ebike__provider__username__icontains=search_query)
        )
        providers = providers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Return counts
    return JsonResponse({
        'bookings_count': bookings.count(),
        'providers_count': providers.count(),
        'approved_bookings': bookings.filter(is_approved=True).count(),
        'pending_bookings': bookings.filter(is_approved=False, is_rejected=False).count(),
        'rejected_bookings': bookings.filter(is_rejected=True).count(),
    })


@user_passes_test(is_admin)
def feedback_list(request):
    """List all contact messages with simple filters."""
    status = request.GET.get('status', 'all')  # all, new, responded
    q = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)

    qs = ContactMessage.objects.all()
    if status == 'new':
        qs = qs.filter(responded=False)
    elif status == 'responded':
        qs = qs.filter(responded=True)
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(email__icontains=q) | Q(subject__icontains=q) | Q(message__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page)
    context = {
        'messages_qs': page_obj.object_list,
        'page_obj': page_obj,
        'current_status': status,
        'q': q,
    }
    return render(request, 'admin_dashboard/feedback_list.html', context)


@user_passes_test(is_admin)
def feedback_detail(request, pk):
    item = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_responded':
            item.responded = True
            item.save()
            messages.success(request, 'Marked as responded.')
            return redirect('admin_feedback_detail', pk=item.pk)
    return render(request, 'admin_dashboard/feedback_detail.html', {'item': item})


@user_passes_test(is_admin)
@require_POST
def feedback_mark_responded(request, pk):
    item = get_object_or_404(ContactMessage, pk=pk)
    item.responded = True
    item.save()
    messages.success(request, 'Feedback marked as responded.')
    return redirect(request.GET.get('next') or 'admin_feedback_list')


@user_passes_test(is_admin)
def reviews_list(request):
    """List and search Reviews with pagination."""
    q = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)
    qs = Review.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(message__icontains=q))
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page)
    return render(request, 'admin_dashboard/reviews_list.html', {
        'reviews': page_obj.object_list,
        'page_obj': page_obj,
        'q': q,
    })


@user_passes_test(is_admin)
def provider_detail(request, provider_id):
    """Admin view: Show provider profile, documents grouped by status, and quick actions."""
    provider = get_object_or_404(User, id=provider_id, is_vehicle_provider=True)
    docs = ProviderDocument.objects.filter(provider=provider).order_by('-uploaded_at')

    pending_docs = docs.filter(status='pending')
    approved_docs = docs.filter(status='approved')
    rejected_docs = docs.filter(status='rejected')

    context = {
        'provider': provider,
        'pending_docs': pending_docs,
        'approved_docs': approved_docs,
        'rejected_docs': rejected_docs,
        'total_docs': docs.count(),
    }
    return render(request, 'admin_dashboard/provider_detail.html', context)
