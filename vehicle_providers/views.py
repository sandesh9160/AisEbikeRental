from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from core.models import EBike, Booking, VehicleRegistration, ProviderDocument, Withdrawal
from .forms import EBikeForm, VehicleRegistrationForm, ProviderDocumentForm, WithdrawalForm
from decimal import Decimal
from django.db.models import Sum
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@login_required
def vehicle_provider_dashboard(request):
    # Get provider's bikes and all bookings (both approved and pending for charts)
    ebikes = EBike.objects.filter(provider=request.user).order_by('-id')
    bookings = Booking.objects.filter(ebike__provider=request.user)
    approved_bookings = bookings.filter(is_approved=True).order_by('-start_date')

    # Calculate provider's total earnings from approved bookings only (optimized DB query)
    total_earnings_result = Booking.objects.filter(
        ebike__provider=request.user, is_approved=True
    ).aggregate(total=Sum('total_price'))['total'] or 0.0
    total_earnings = Decimal(str(total_earnings_result))

    # Apply platform fee (10%) - this is deducted by the platform
    platform_charges = total_earnings * Decimal('0.10')

    # Net earnings after platform fee
    net_earnings = total_earnings - platform_charges

    # Only subtract pending and approved withdrawals (exclude completed - already paid)
    pending_withdrawals_total = Withdrawal.objects.filter(
        provider=request.user,
        status__in=['pending', 'approved']  # Exclude 'completed' - already paid
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')

    # Get registration fee status - one-time fee providers must pay
    registration_fee = Decimal('100.00')
    registration_fee_paid = request.user.registration_fee_paid

    # Available balance after platform fees and pending/approved withdrawals
    available_balance = max(net_earnings - pending_withdrawals_total, Decimal('0.0'))

    # Registration fee handling - providers must have paid ₹100 fee to be able to withdraw
    if not registration_fee_paid:
        # If registration fee not paid, deduct it from available balance
        if available_balance >= registration_fee:
            available_balance_after_fee = available_balance - registration_fee
            can_withdraw = available_balance_after_fee > Decimal('0.0')
        else:
            available_balance_after_fee = Decimal('0.0')
            can_withdraw = False

        ready_for_withdrawal = available_balance_after_fee if can_withdraw else Decimal('0.0')
    else:
        # Registration fee already paid, check if balance > 0
        can_withdraw = available_balance > Decimal('0.0')
        ready_for_withdrawal = available_balance if can_withdraw else Decimal('0.0')
        registration_fee_status = "Registration Fee Paid ✓"

    # Status message
    if not registration_fee_paid:
        if available_balance < registration_fee:
            status_message = "Registration Fee Required"
            status_detail = f"Pay ₹{registration_fee}.00 to start earning"
        else:
            status_message = "Ready for Withdrawal"
            status_detail = f"₹{ready_for_withdrawal:.0f} available" if ready_for_withdrawal > 0 else "Insufficient funds"
    else:
        status_message = "Ready for Withdrawal" if can_withdraw else "Low Balance"
        status_detail = f"₹{ready_for_withdrawal:.0f} available" if ready_for_withdrawal > 0 else "Balance too low"

    print(f"TEMP FIX ACTIVE: net_earnings={net_earnings}, available_balance={available_balance}, ready={ready_for_withdrawal}")

    # Add debug logging to verify balance calculation
    print("=" * 60)
    print("🔍 PROVIDER DASHBOARD BALANCE DEBUG")
    print("=" * 60)
    print(f"👤 Provider: {request.user.username} (ID: {request.user.id})")
    print(f"📊 Total Bookings: {bookings.count()} | Approved: {approved_bookings.count()}")
    print(f"💰 Total Earnings Result: {total_earnings_result}")
    print(f"💰 Total Earnings: ₹{total_earnings}")
    print(f"➖ Platform Charges (10%): ₹{platform_charges}")
    print(f"💵 Net Earnings: ₹{net_earnings}")
    print(f"💸 Pending/Approved Withdrawals Total: ₹{pending_withdrawals_total}")
    print(f"💰 Available Balance: ₹{available_balance}")
    print(f"🛡️  Registration Fee Paid: {registration_fee_paid}")
    print(f"🎯 Ready for Withdrawal: ₹{ready_for_withdrawal}")
    print(f"✅ Can Withdraw: {can_withdraw}")
    print(f"📝 Status Message: {status_message}")
    print(f"📋 Status Detail: {status_detail}")
    print("=" * 60)

    # Also show recent booking data
    if approved_bookings.exists():
        print("🎫 RECENT APPROVED BOOKINGS:")
        for booking in approved_bookings[:3]:
            print(f"  • Booking #{booking.id} - ₹{booking.total_price} - {booking.rider.username}")
    else:
        print("⚠️  No approved bookings found!")

    # Show withdrawal status
    recent_withdrawals = Withdrawal.objects.filter(provider=request.user).order_by('-created_at')[:3]
    if recent_withdrawals.exists():
        print("💳 RECENT WITHDRAWALS:")
        for withdrawal in recent_withdrawals:
            print(f"  • Withdrawal #{withdrawal.id} - ₹{withdrawal.amount} - Status: {withdrawal.status}")
    print("=" * 60)

    # Get recent withdrawal status for transaction tracking
    recent_withdrawals_status = Withdrawal.objects.filter(provider=request.user).order_by('-created_at')[:3]

    # Calculate performance metrics
    ebikes_count = ebikes.count()
    approved_bookings_count = approved_bookings.count()

    per_bike_earnings = Decimal('0.00')
    per_booking_earnings = Decimal('0.00')
    fleet_utilization = Decimal('0.00')

    if ebikes_count > 0:
        per_bike_earnings = total_earnings / ebikes_count

        if ebikes_count > 0:
            fleet_utilization = (approved_bookings_count / ebikes_count) * 100

    if approved_bookings_count > 0:
        per_booking_earnings = total_earnings / approved_bookings_count

    # Balance calculation summary for transparency
    # available_balance = earnings - platform_fees - pending_withdrawals - registration_fee

    # Define minimum reserve for withdrawal calculation
    registration_fee = Decimal('100.00')
    if not registration_fee_paid:
        minimum_reserve = registration_fee  # Must pay registration fee first
    else:
        minimum_reserve = Decimal('0.00')  # No minimum reserve once registration fee is paid

    # Calculate additional amount needed for withdrawal eligibility
    additional_needed = max(minimum_reserve - available_balance, Decimal('0.00'))

    return render(request, 'vehicle_providers/dashboard.html', {
        'ebikes': ebikes,
        'approved_bookings': approved_bookings,
        'bookings': bookings,
        'total_earnings': total_earnings,
        'platform_charges': platform_charges,
        'net_earnings': net_earnings,
        'available_balance': available_balance,
        'can_withdraw': can_withdraw,
        'ready_for_withdrawal': ready_for_withdrawal,
        'status_message': status_message,
        'status_detail': status_detail,
        'registration_fee_paid': registration_fee_paid,
        'recent_withdrawals_status': recent_withdrawals_status,
        'per_bike_earnings': per_bike_earnings,
        'per_booking_earnings': per_booking_earnings,
        'fleet_utilization': fleet_utilization,
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

            # Notify admin about new document upload
            subject = 'New Document Uploaded for Verification'
            context = {'document': document}
            html_message = render_to_string('emails/document_uploaded.html', context)
            plain_message = f"""
            New document uploaded by {document.provider.get_full_name() or document.provider.username}.

            Document Type: {document.get_document_type_display()}
            Document Number: {document.document_number or 'Not provided'}
            Provider: {document.provider.username} ({document.provider.email})

            Please review this document in the admin dashboard.
            """
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True
            )

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


@login_required
def request_withdrawal(request):
    if not request.user.is_vehicle_provider:
        messages.error(request, 'Only vehicle providers can request withdrawals.')
        return redirect('vehicle_provider_dashboard')

    # Calculate available balance same as dashboard (FIXED: exclude completed withdrawals)
    total_earnings_result = Booking.objects.filter(
        ebike__provider=request.user, is_approved=True
    ).aggregate(total=Sum('total_price'))['total'] or 0.0
    total_earnings = Decimal(str(total_earnings_result))

    platform_charges = total_earnings * Decimal('0.10')

    # FIX: Only subtract pending and approved withdrawals, not completed ones
    pending_withdrawals_total = Withdrawal.objects.filter(
        provider=request.user,
        status__in=['pending', 'approved']  # Exclude completed - already paid
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')

    available_balance = max(total_earnings - platform_charges - pending_withdrawals_total, Decimal('0.0'))

    # Update MINIMUM_RESERVE to use registration_fee instead of fixed 100
    registration_fee = Decimal('100.00')
    if not request.user.registration_fee_paid:
        MINIMUM_RESERVE = registration_fee  # Must pay registration fee first
        can_withdraw = available_balance > MINIMUM_RESERVE and available_balance - MINIMUM_RESERVE > 0
        withdrawable_balance = max(available_balance - MINIMUM_RESERVE, Decimal('0.0')) if can_withdraw else Decimal('0.0')
    else:
        MINIMUM_RESERVE = Decimal('0.00')  # No minimum reserve once registration fee is paid
        can_withdraw = available_balance > Decimal('0.0')
        withdrawable_balance = available_balance if can_withdraw else Decimal('0.0')

    # Calculate additional amount needed
    additional_needed = max(MINIMUM_RESERVE - available_balance, Decimal('0.00'))

    # FIX: Dynamic minimum withdrawal - use the lesser of standard minimum or what's available
    MIN_WITHDRAWAL = Decimal('200.00')
    effective_min_withdrawal = min(MIN_WITHDRAWAL, withdrawable_balance) if can_withdraw else MIN_WITHDRAWAL

    if not can_withdraw:
        if not request.user.registration_fee_paid:
            messages.error(f'Insufficient balance. You need to pay the ₹{registration_fee} registration fee first.')
        else:
            messages.error('Insufficient balance for withdrawal.')
        return redirect('vehicle_provider_dashboard')

    if request.method == 'POST':
        amount_requested = Decimal(request.POST.get('amount', '0'))

        # Validate withdrawal amount using effective minimum
        if amount_requested < effective_min_withdrawal:
            messages.error(request, f'Minimum withdrawal amount is ₹{effective_min_withdrawal}.')
            return redirect('request_withdrawal')

        if amount_requested > withdrawable_balance:
            messages.error(request, f'Insufficient balance. Maximum withdrawable: ₹{withdrawable_balance:.2f}')
            return redirect('request_withdrawal')

        form = WithdrawalForm(request.POST, provider=request.user)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.provider = request.user
            transfer_type = request.POST.get('transfer_type', 'bank')

            # Clear fields based on transfer type
            if transfer_type == 'upi':
                withdrawal.ifsc_code = None
                withdrawal.bank_name = None
            else:
                withdrawal.upi_id = None

            withdrawal.save()

            # Notify admin about new withdrawal request
            subject = 'New Withdrawal Request Submitted'
            context = {'withdrawal': withdrawal}
            html_message = render_to_string('emails/withdrawal_request.html', context)
            plain_message = f"""
            New withdrawal request submitted by {withdrawal.provider.get_full_name() or withdrawal.provider.username}.

            Amount: ₹{withdrawal.amount}
            Account Holder: {withdrawal.account_holder_name}
            Account Number: {withdrawal.account_number}
            Bank: {withdrawal.bank_name}
            IFSC: {withdrawal.ifsc_code}

            Please review and process this withdrawal request in the admin dashboard.
            """
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True
            )

            messages.success(request, f'Withdrawal request of ₹{withdrawal.amount} submitted successfully! It will be processed by admin.')
            return redirect('vehicle_provider_dashboard')
    else:
        form = WithdrawalForm(provider=request.user)

    return render(request, 'vehicle_providers/request_withdrawal.html', {
        'form': form,
        'available_balance': available_balance,
        'withdrawable_balance': withdrawable_balance,
        'minimum_reserve': MINIMUM_RESERVE,
        'total_earnings': total_earnings,
        'platform_charges': platform_charges,
        'can_withdraw': can_withdraw,
        'additional_needed': additional_needed,
        'effective_min_withdrawal': effective_min_withdrawal,
    })


@login_required
def withdrawal_history(request):
    if not request.user.is_vehicle_provider:
        messages.error(request, 'Only vehicle providers can view withdrawal history.')
        return redirect('vehicle_provider_dashboard')

    withdrawals = Withdrawal.objects.filter(provider=request.user).order_by('-created_at')

    return render(request, 'vehicle_providers/withdrawal_history.html', {
        'withdrawals': withdrawals,
    })


@login_required
def download_withdrawal_receipt(request, withdrawal_id):
    """
    Generate and return a PDF receipt for the withdrawal.

    Args:
        request: The HTTP request object
        withdrawal_id: ID of the withdrawal to generate receipt for

    Returns:
        HttpResponse: PDF receipt as attachment or redirect with error message
    """
    try:
        # Get the withdrawal or return 404
        withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id, provider=request.user)

        # Check if withdrawal is completed
        if withdrawal.status != 'completed':
            messages.error('Receipt is only available for completed withdrawals.')
            return redirect('withdrawal_history')

        # Import required libraries
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        import os
        from datetime import datetime
        from decimal import Decimal
        import qrcode

        # Initialize PDF buffer and canvas
        buffer = BytesIO()
        width, height = A4
        p = canvas.Canvas(buffer, pagesize=A4)

        # --- Ultra Modern Styling constants with enhanced layout ---
        card_x = 12
        top_margin = 12
        card_width = width - 2 * card_x
        card_height = 750  # Significantly increased to eliminate all overlapping
        card_y = height - card_height - top_margin
        padding = 32
        section_gap = 40
        line_height = 24
        title_font = "Helvetica-Bold"
        label_font = "Helvetica-Bold"
        value_font = "Helvetica-Bold"  # Made bold for currency visibility
        rup_font = "Symbol"            # Changed to Symbol font for better rupee visibility
        highlight_color = colors.HexColor('#00D4AA')  # Modern teal
        header_color = colors.HexColor('#1a202c')     # Dark slate
        success_color = colors.HexColor('#38a169')    # Green
        accent_color = colors.HexColor('#3182ce')     # Blue accent
        meta_color = colors.HexColor('#718096')       # Gray
        bg_color = colors.HexColor('#f8fafc')         # Off-white bg
        card_bg_color = colors.white
        border_color = colors.HexColor('#cbd5e0')     # Light blue border
        section_bg = colors.HexColor('#f7fafc')       # Section backgrounds

        # --- Background and main card ---
        p.setFillColor(bg_color)
        p.rect(0, 0, width, height, fill=1, stroke=0)
        p.setFillColor(card_bg_color)
        p.setStrokeColor(border_color)
        p.setLineWidth(1.5)
        p.roundRect(card_x, card_y, card_width, card_height, 12, fill=1, stroke=1)

        # --- Header Section ---
        header_height = 80
        y = card_y + card_height - padding

        # Header background gradient effect
        p.setFillColor(header_color)
        p.roundRect(card_x, y - header_height, card_width, header_height, 12, fill=1, stroke=0)

        # Add decorative elements
        p.setFillColor(highlight_color)
        p.circle(card_x + 30, y - 25, 8, fill=1, stroke=0)  # Left circle
        p.circle(card_x + card_width - 30, y - 25, 6, fill=1, stroke=0)  # Right circle

        # Company title
        p.setFillColor(colors.white)
        p.setFont(title_font, 28)
        p.drawCentredString(card_x + card_width/2, y - header_height + 40, "AIS E-BIKE RENTAL")

        # Subtitle and date
        p.setFont(value_font, 14)
        receipt_date = timezone.now().strftime('%B %d, %Y')
        p.drawCentredString(card_x + card_width/2, y - header_height + 15, f"Withdrawal Receipt - {receipt_date}")

        # Transaction success banner
        banner_height = 25
        banner_y = y - header_height - 10
        p.setFillColor(colors.green)
        p.roundRect(card_x + padding, banner_y - banner_height, card_width - 2*padding, banner_height, 8, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont(label_font, 11)
        p.drawCentredString(card_x + card_width/2, banner_y - banner_height + 8, "✓ TRANSACTION COMPLETED SUCCESSFULLY")

        y = banner_y - banner_height - section_gap

        # --- Provider Information Section ---
        p.setFont(label_font, 16)
        p.setFillColor(header_color)
        p.drawString(card_x + padding, y, "Provider Information")
        y -= (line_height + 5)

        # Provider details box with border
        box_height = 70
        p.setFillColor(colors.white)
        p.setStrokeColor(colors.HexColor('#cbd5e0'))
        p.setLineWidth(1)
        p.roundRect(card_x + padding, y - box_height, card_width - 2 * padding, box_height, 8, fill=1, stroke=1)

        # Provider details
        detail_x = card_x + padding + 15
        p.setFont(label_font, 13)
        p.setFillColor(colors.black)
        p.drawString(detail_x, y - 20, withdrawal.provider.get_full_name() or withdrawal.provider.username)
        p.setFont(value_font, 12)
        p.setFillColor(meta_color)
        p.drawString(detail_x, y - 38, f"Provider ID: {withdrawal.provider.username}")
        p.drawString(detail_x, y - 55, f"Email: {withdrawal.provider.email}")
        y -= (box_height + section_gap)

        # --- Amount Details Section with Modern Styling ---
        p.setFont(label_font, 16)
        p.setFillColor(header_color)
        p.drawString(card_x + padding, y, "Transaction Summary")
        y -= (line_height + 8)

        # Create amount display box with modern borders
        amount_box_height = 90
        p.setFillColor(section_bg)
        p.setStrokeColor(accent_color)
        p.setLineWidth(1.5)
        p.roundRect(card_x + padding, y - amount_box_height, card_width - 2*padding, amount_box_height, 10, fill=1, stroke=1)

        # Withdrawal Amount - Large, prominent with clear rupee symbol
        amt_y = y - 25
        p.setFont(value_font, 12)
        p.setFillColor(colors.black)
        p.drawString(card_x + padding + 15, amt_y, "Principal Amount:")
        p.setFont(label_font, 18)
        p.setFillColor(accent_color)
        principal_amount = f"₹ {withdrawal.amount:,.2f}"
        p.drawRightString(card_x + card_width - padding - 15, amt_y, principal_amount)

        # Platform charges - Clear display
        charge_y = amt_y - 25
        p.setFont(value_font, 11)
        p.setFillColor(meta_color)
        p.drawString(card_x + padding + 15, charge_y, "Transaction Fee (2%):")
        platform_charges = Decimal(str(withdrawal.amount)) * Decimal('0.02')
        fee_amount = f"₹ {platform_charges:,.2f}"
        p.setFont(label_font, 13)
        p.setFillColor(colors.HexColor('#e53e3e'))  # Red for fee
        p.drawRightString(card_x + card_width - padding - 15, charge_y, fee_amount)

        # Net Amount - Highlighted, large and clear
        net_y = charge_y - 28
        p.setFont(label_font, 14)
        p.setFillColor(success_color)
        p.drawString(card_x + padding + 15, net_y, "Net Amount Received:")
        net_amount = withdrawal.amount - platform_charges
        net_amount_str = f"₹ {net_amount:,.2f}"
        p.setFont(label_font, 16)
        p.setFillColor(success_color)
        p.drawRightString(card_x + card_width - padding - 15, net_y, net_amount_str)

        # Add decorative line
        p.setStrokeColor(highlight_color)
        p.setLineWidth(0.5)
        p.line(card_x + padding + 10, net_y - 8, card_x + card_width - padding - 10, net_y - 8)

        y -= (amount_box_height + section_gap)

        y -= (section_gap)

        # Account and Transaction Details
        p.setFont(label_font, 13)
        p.setFillColor(header_color)
        p.drawString(card_x + padding, y, "Payment Details")
        y -= (line_height + 5)

        # Status
        p.setFont(value_font, 12)
        p.setFillColor(colors.black)
        status_text = "SUCCESSFUL" if withdrawal.status == 'completed' else withdrawal.status.upper()
        if withdrawal.status == 'completed':
            p.setFillColor(colors.green)
        p.drawString(card_x + padding, y, f"Status: {status_text}")
        y -= line_height

        # Transaction ID
        if withdrawal.transaction_id:
            p.setFillColor(colors.black)
            p.drawString(card_x + padding, y, f"Transaction ID: {withdrawal.transaction_id}")
            y -= line_height

        # Account details
        p.setFont(value_font, 10)
        p.setFillColor(meta_color)
        p.drawString(card_x + padding, y, f"Account Holder: {withdrawal.account_holder_name}")
        y -= line_height
        if withdrawal.upi_id:
            p.drawString(card_x + padding, y, f"Payment Method: UPI ({withdrawal.upi_id})")
        else:
            p.drawString(card_x + padding, y, f"Bank: {withdrawal.bank_name}")
            y -= line_height
            p.drawString(card_x + padding, y, f"Account: {withdrawal.account_number[-4:] if withdrawal.account_number else 'XXXX'}...{withdrawal.ifsc_code}")
        y -= section_gap

        # --- Authorization Section with Signature, Stamp & QR Code ---
        # Position it well below all other content to prevent overlapping
        auth_section_start = card_y + 60  # Start authorization section 60px from card bottom

        # Left side - Company Logo & Info (at bottom left)
        logo_x = card_x + padding + 10
        logo_y = auth_section_start + 50

        # AIS Logo placeholder
        p.setFillColor(header_color)
        p.roundRect(logo_x, logo_y - 35, 45, 35, 6, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont(title_font, 14)
        p.drawCentredString(logo_x + 22.5, logo_y - 20, "AIS")

        # Company Info (to the right of logo)
        company_info_x = logo_x + 55
        p.setFillColor(meta_color)
        p.setFont(value_font, 7)
        p.drawString(company_info_x, logo_y - 12, "AIS E-Bike Rental Services Pvt. Ltd.")
        p.drawString(company_info_x, logo_y - 22, "GSTIN: 29ABCDE1234F1Z5 | CIN: U12345KA2023PTC123456")
        p.drawString(company_info_x, logo_y - 32, "support@aisebike.com")

        # Right side - QR Code (at bottom right)
        qr_code_x = card_x + card_width - padding - 50

        # Try to generate real QR code, fallback to placeholder if not available
        qr_generated = False
        try:
            # Generate real QR code with transaction data
            qr_data = f"""AIS E-BIKE RENTAL
TRANSACTION VERIFICATION
ID: {withdrawal.transaction_id or f"W{withdrawal.id:06d}"}
Provider: {withdrawal.provider.username}
Amount: ₹{withdrawal.amount}
Status: {withdrawal.status.title()}
Date: {withdrawal.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Verified by AIS E-Bike Rental"""

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=1,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Generate QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)

            # Draw the QR code on PDF
            qr_image_data = qr_buffer.getvalue()
            qr_image = ImageReader(BytesIO(qr_image_data))

            # Position QR code (35x35 pixels matches our layout)
            p.drawImage(qr_image, qr_code_x, logo_y - 35, width=35, height=35, mask='auto')
            qr_generated = True

        except ImportError:
            # Fallback to simple QR placeholder if libraries not available
            qr_generated = False

        # Draw QR code (real or placeholder)
        if not qr_generated:
            # Simple QR Code placeholder representation
            p.setStrokeColor(accent_color)
            p.setLineWidth(1.2)
            p.rect(qr_code_x, logo_y - 35, 35, 35, fill=0, stroke=1)
            # Inner pattern
            p.rect(qr_code_x + 3, logo_y - 33, 10, 10, fill=1, stroke=0)
            p.rect(qr_code_x + 22, logo_y - 33, 10, 10, fill=1, stroke=0)
            p.rect(qr_code_x + 3, logo_y - 10, 29, 7, fill=1, stroke=0)

        # QR verification text
        p.setFillColor(meta_color)
        p.setFont(value_font, 5)
        p.drawCentredString(qr_code_x + 17.5, logo_y - 40, "SCAN TO VERIFY")

        # Signature section (middle area)
        signature_y = card_y + 30

        # Authorized Signature (center left)
        signature_x = card_x + padding + 100
        p.setStrokeColor(colors.black)
        p.setLineWidth(1.2)
        p.line(signature_x, signature_y, signature_x + 70, signature_y)

        p.setFillColor(meta_color)
        p.setFont(value_font, 8)
        p.drawCentredString(signature_x + 35, signature_y + 5, "Authorized Signatory")

        # Company Stamp (center right)
        stamp_x = qr_code_x - 20
        stamp_y = signature_y - 5

        # Stamp circle
        p.setFillColor(colors.HexColor('#f9fafb'))
        p.circle(stamp_x, stamp_y, 20, fill=1, stroke=0)
        p.setStrokeColor(header_color)
        p.setLineWidth(1.5)
        p.circle(stamp_x, stamp_y, 20, fill=0, stroke=1)

        # Stamp content
        p.setFillColor(header_color)
        p.setFont(label_font, 8)
        p.drawCentredString(stamp_x, stamp_y + 5, "APPROVED")
        p.setFont(value_font, 5)
        p.drawCentredString(stamp_x, stamp_y + 1, "AIS E-BIKE")
        p.drawCentredString(stamp_x, stamp_y - 3, "ADMIN")

        # Date stamp
        p.setFont(value_font, 6)
        date_stamp = timezone.now().strftime('%d/%m/%Y')
        p.drawCentredString(stamp_x, stamp_y - 10, date_stamp)

        # Bottom Footer (very bottom)
        footer_y = card_y + 12
        p.setFillColor(meta_color)
        p.setFont(value_font, 7)
        p.drawCentredString(card_x + card_width / 2, footer_y, "This is a computer-generated receipt. No signature required for verification.")
        p.drawCentredString(card_x + card_width / 2, footer_y - 8, "AIS E-Bike Rental Services - Making electric mobility accessible")

        p.showPage()
        p.save()
        buffer.seek(0)

        # Set up response
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="withdrawal_receipt_{withdrawal.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response

    except Exception as e:
        # Log the error
        logger.error(f"Error generating withdrawal receipt for withdrawal {withdrawal_id}: {str(e)}")

        # Show error message to user
        messages.error(request, f"Error generating receipt: {str(e)}")
        return redirect('withdrawal_history')
