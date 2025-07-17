from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Booking, EBike, Notification, User
from .forms import BookingForm
from django.contrib import messages
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def rider_dashboard(request):
    bookings = Booking.objects.filter(rider=request.user)  # Get bookings for the current rider
    # All e-bikes that are booked (approved) by any rider
    all_booked_ebikes = EBike.objects.filter(bookings__is_approved=True).distinct()
    # Only show e-bikes that are available and not already booked by anyone
    available_ebikes = EBike.objects.filter(is_available=True).exclude(id__in=all_booked_ebikes.values_list('id', flat=True))
    user_booked_ids = list(bookings.values_list('ebike_id', flat=True))
    unread_notification_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    return render(request, 'riders/dashboard.html', {
        'bookings': bookings,
        'already_booked_ebikes': all_booked_ebikes,
        'user_booked_ids': user_booked_ids,
        'available_ebikes': available_ebikes,
        'unread_notification_count': unread_notification_count,
        'notifications': notifications,
    })

@login_required
def book_ebike(request, ebike_id):
    ebike = EBike.objects.get(id=ebike_id)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            total_days = (end_date - start_date).days
            total_price = total_days * ebike.price_per_day 

            if total_days < 1 or total_price <= 0:
                messages.error(request, 'Please select a valid date range. Booking must be at least 1 day and total amount must be greater than ₹0.')
                return render(request, 'riders/book_bike.html', {'form': form, 'ebike': ebike})

            # Create booking instance but don't save yet
            booking = form.save(commit=False)
            booking.total_price = total_price
            booking.ebike = ebike
            booking.rider = request.user  # Set the rider to the currently logged-in user
            booking.save()

            # Notify all admins
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    message=f"New booking by {request.user.username} for {ebike.name}.",
                    link=f"/admin-dashboard/#bookings"
                )

            return redirect('payment', booking_id=booking.id)
    else:
        form = BookingForm()

    return render(request, 'riders/book_bike.html', {'form': form, 'ebike': ebike})

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, rider=request.user)
    return render(request, 'riders/booking_confirmation.html', {'booking': booking})

@login_required
def payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, rider=request.user)
    if booking.is_paid:
        messages.info(request, 'This booking is already paid.')
        return redirect('booking_confirmation', booking_id=booking.id)
    if request.method == 'POST':
        # Simulate payment success
        booking.is_paid = True
        booking.save()
        messages.success(request, 'Payment successful!')
        return redirect('booking_confirmation', booking_id=booking.id)
    return render(request, 'riders/payment.html', {'booking': booking})

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)

@login_required
def download_receipt(request, booking_id):
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    import os
    import qrcode
    from io import BytesIO
    from datetime import datetime
    booking = get_object_or_404(Booking, id=booking_id, rider=request.user)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- Styling constants ---
    card_x = 30
    top_margin = 30
    card_width = width - 2 * card_x
    card_height = 420  # Keep as before for content fit
    card_y = height - card_height - top_margin  # Place card at the top of the page
    padding = 18
    section_gap = 24
    line_height = 18
    label_font = "Helvetica-Bold"
    value_font = "Helvetica"
    highlight_color = colors.HexColor('#00BFA6')
    header_color = colors.HexColor('#0D47A1')
    meta_color = colors.HexColor('#888888')
    bg_color = colors.HexColor('#f9f9f9')
    card_bg_color = colors.HexColor('#f4f6fa')
    status_paid_color = colors.HexColor('#00BFA6')
    platform_charge = Decimal('20.00')

    # --- Card background with border ---
    p.setFillColor(bg_color)
    p.rect(0, 0, width, height, fill=1, stroke=0)
    p.setFillColor(card_bg_color)
    border_color = highlight_color
    p.setStrokeColor(border_color)
    p.setLineWidth(2)
    p.roundRect(card_x, card_y, card_width, card_height, 20, fill=1, stroke=1)

    # --- All content inside the card ---
    y = card_y + card_height - padding

    # Header with brand logo and title (inside card)
    header_height = 70
    brand_logo_path = os.path.join('media', 'brand_logo.png')
    if os.path.exists(brand_logo_path):
        p.drawImage(brand_logo_path, card_x + padding, y - header_height + 10, 50, 50, mask='auto')
    else:
        # Draw a placeholder rectangle and text if logo is missing
        p.setFillColor(colors.HexColor('#cccccc'))
        p.rect(card_x + padding, y - header_height + 10, 50, 50, fill=1, stroke=0)
        p.setFillColor(colors.black)
        p.setFont("Helvetica", 8)
        p.drawString(card_x + padding + 5, y - header_height + 35, "No Logo")
    p.setFillColor(header_color)
    p.roundRect(card_x, y - header_height, card_width, header_height, 20, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(card_x + padding + 60, y - header_height + 35, "AIS E-BIKE RENTAL")
    p.setFont("Helvetica", 12)
    p.drawString(card_x + padding + 60, y - header_height + 15, "Booking Receipt")
    y -= header_height + section_gap

    # Billing to with user logo
    p.setFont(label_font, 14)
    p.setFillColor(header_color)
    p.drawString(card_x + padding, y, "Billing to")
    user_logo_path = booking.rider.profile_image.path if hasattr(booking.rider, 'profile_image') and booking.rider.profile_image and os.path.exists(booking.rider.profile_image.path) else None
    if user_logo_path:
        p.drawImage(user_logo_path, card_x + padding + 90, y - 10, 32, 32, mask='auto')
        text_x = card_x + padding + 130
    else:
        text_x = card_x + padding + 90
    p.setFont(value_font, 12)
    p.setFillColor(colors.black)
    p.drawString(text_x, y, booking.rider.get_full_name() or booking.rider.username)
    p.setFont(value_font, 10)
    p.setFillColor(meta_color)
    p.drawString(text_x, y - line_height, f"📧 {booking.rider.email}")
    p.drawString(text_x, y - 2 * line_height, f"☎ {getattr(booking.rider, 'mobile_number', '')}")
    y -= (section_gap + 2 * line_height)

    # Booking Details Section
    p.setFont(label_font, 14)
    p.setFillColor(header_color)
    p.drawString(card_x + padding, y, "Booking Details")
    y -= (line_height + 10)
    p.setFillColor(colors.white)
    p.roundRect(card_x + padding, y - 90, card_width - 2 * padding, 90, 12, fill=1, stroke=0)
    ebike_img_path = booking.ebike.image.path if booking.ebike.image and os.path.exists(booking.ebike.image.path) else None
    # Draw only the e-bike image (no user profile image here)
    if ebike_img_path:
        p.drawImage(ebike_img_path, card_x + padding + 10, y - 80, 70, 70, mask='auto')
    p.setFont(label_font, 12)
    p.setFillColor(colors.black)
    p.drawString(card_x + padding + 90, y - 30, f" {booking.ebike.name}")
    p.setFont(value_font, 11)
    p.setFillColor(meta_color)
    date_fmt = lambda d: datetime.strftime(d, '%d %b %Y')
    p.drawString(card_x + padding + 90, y - 50, f" {date_fmt(booking.start_date)} to {date_fmt(booking.end_date)}")
    p.setFillColor(colors.black)
    p.drawString(card_x + padding + 90, y - 70, f"RS.{booking.total_price:.2f}")
    p.setFillColor(status_paid_color)
    p.roundRect(card_x + card_width - 2 * padding - 70, y - 40, 50, 22, 10, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont(label_font, 11)
    p.drawCentredString(card_x + card_width - 2 * padding - 45, y - 27, "✅ Paid")
    qr_data = f"BookingID:{booking.id}|User:{booking.rider.username}|Bike:{booking.ebike.name}|From:{date_fmt(booking.start_date)}|To:{date_fmt(booking.end_date)}|Amount:{(booking.total_price + platform_charge):.2f}"
    qr = qrcode.make(qr_data)
    qr_io = BytesIO()
    qr.save(qr_io, kind='PNG')
    qr_io.seek(0)
    qr_img = ImageReader(qr_io)
    p.drawImage(qr_img, card_x + card_width - 2 * padding - 70, y - 80, 50, 50, mask='auto')
    y -= (100 + section_gap)

    # Payment Section
    p.setFont(label_font, 13)
    p.setFillColor(header_color)
    p.drawString(card_x + padding, y, "Payment Received")
    y -= (line_height + 5)
    p.setFont(value_font, 11)
    p.setFillColor(colors.black)
    p.drawString(card_x + padding, y, "Rental amount")
    p.drawRightString(card_x + card_width - padding, y, f" RS.{booking.total_price:.2f}")
    y -= line_height
    p.setFillColor(meta_color)
    p.drawString(card_x + padding, y, "Platform charges")
    p.drawRightString(card_x + card_width - padding, y, f" RS.{platform_charge:.2f}")
    y -= line_height
    p.setFont(label_font, 12)
    p.setFillColor(highlight_color)
    p.drawString(card_x + padding, y, "Total")
    p.setFillColor(colors.black)
    p.setFont(label_font, 12)
    p.drawRightString(card_x + card_width - padding, y, f" RS.{(booking.total_price + platform_charge):.2f}")
    y -= (section_gap)

    # Footer (inside card)
    p.setFont(value_font, 9)
    p.setFillColor(meta_color)
    p.drawCentredString(card_x + card_width / 2, card_y + 20, "AIS E-Bike Rental | GSTIN: 29ABCDE1234F1Z5 | CIN: U12345KA2023PTC123456 | Contact: support@aisebike.com")
    p.drawCentredString(card_x + card_width / 2, card_y + 8, "This is a computer-generated receipt. No signature required.")

    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_booking_{booking.id}.pdf"'
    return response

