from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Booking, EBike, Notification, User
from .forms import BookingForm
from django.contrib import messages
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

import razorpay
import json
from razorpay import utility


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
            # Proceed to payment page for this booking
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
    
    # Development bypass for rate limiting issues
    if settings.DEBUG and request.GET.get('skip_payment') == 'true':
        booking.is_paid = True
        booking.save(update_fields=["is_paid"])
        messages.success(request, 'Payment bypassed for development testing.')
        return redirect('booking_confirmation', booking_id=booking.id)
    # Ensure Razorpay keys are configured
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    not_configured = (not key_id or not key_secret or 'xxxxxxxx' in key_id or 'xxxxxxxx' in key_secret)
    if not_configured:
        messages.error(request, 'Razorpay keys are not configured. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in environment.')
        return render(request, 'riders/payment.html', {
            'booking': booking,
            'payment_error': 'Razorpay is not configured. Contact support.',
        })
    # Create a Razorpay Order for this booking (amount in paise)
    amount_paise = int(Decimal(booking.total_price) * 100)
    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        order = client.order.create(dict(
            amount=amount_paise,
            currency="INR",
            receipt=str(booking.id),
            notes={"booking_id": str(booking.id), "user": request.user.username},
            payment_capture=1,
        ))
        masked_key = key_id if not key_id else (key_id[:7] + '...' + key_id[-4:])
        context = {
            'booking': booking,
            'razorpay_key_id': key_id,
            'razorpay_order_id': order.get('id'),
            'amount_paise': amount_paise,
            'currency': 'INR',
            'customer_name': request.user.get_full_name() or request.user.username,
            'customer_email': request.user.email,
            'customer_contact': getattr(request.user, 'mobile_number', ''),
        }
        if settings.DEBUG:
            context['payment_debug'] = {
                'is_paid': booking.is_paid,
                'key_loaded': bool(key_id),
                'key_masked': masked_key,
                'order_id_present': bool(order.get('id')),
            }
        return render(request, 'riders/payment.html', context)
    except razorpay.errors.BadRequestError:
        messages.error(request, 'Payment initialization failed. Please try again later.')
        return render(request, 'riders/payment.html', {
            'booking': booking,
            'payment_error': 'Authentication failed with Razorpay. Check API keys.',
        })


@login_required
@require_POST
def verify_razorpay_payment(request, booking_id):
    """Verify Razorpay payment signature and update booking status."""
    booking = get_object_or_404(Booking, id=booking_id, rider=request.user)
    
    try:
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        # Verify payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, key_secret))
        try:
            client.utility.verify_payment_signature(params_dict)
            
            # Payment successful, update booking status
            booking.is_paid = True
            booking.status = 'pending'  # Set initial status to pending
            booking.razorpay_payment_id = razorpay_payment_id
            booking.razorpay_order_id = razorpay_order_id
            booking.save(update_fields=['is_paid', 'status', 'razorpay_payment_id', 'razorpay_order_id'])
            
            # Send confirmation email
            try:
                send_booking_confirmation_email(booking)
            except Exception as e:
                # Log email error but don't fail the payment verification
                import logging
                logging.error(f"Failed to send confirmation email for booking {booking.id}: {str(e)}")
                # Continue with the payment verification process
            
            # Notify admin
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    message=f"New booking by {request.user.username} for {booking.ebike.name} is pending approval.",
                    link=f"/admin-dashboard/"
                )
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('booking_confirmation', kwargs={'booking_id': booking.id})
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Payment verification failed: ' + str(e)
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)


def send_booking_confirmation_email(booking):
    """Send booking confirmation email to the user."""
    try:
        subject = f"Booking Confirmation - #{booking.id}"

        # Render HTML email template
        html_message = render_to_string('emails/booking_confirmation.html', {
            'booking': booking,
            'user': booking.rider,
            'site_name': 'AIS E-Bike Rental'
        })

        # Create plain text version
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.rider.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        # Log the error for debugging
        import logging
        logging.error(f"Failed to send confirmation email for booking {booking.id}: {str(e)}")
        # Re-raise the exception so it can be caught by the calling function
        raise e


@login_required
@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhooks for robust server-to-server confirmation.

    Expects header 'X-Razorpay-Signature'. On 'payment.captured', fetch the Order to
    read its 'receipt' (we set it to the booking id) and mark Booking.is_paid=True.
    """
    try:
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        if not signature:
            return JsonResponse({"success": False, "error": "Missing signature"}, status=400)
        body = request.body.decode('utf-8')
        # Verify webhook signature
        utility.verify_webhook_signature(body, signature, settings.RAZORPAY_WEBHOOK_SECRET)
        payload = json.loads(body)
        event = payload.get('event')
        if event == 'payment.captured':
            payment = payload.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment.get('order_id')
            if order_id:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                try:
                    order = client.order.fetch(order_id)
                    receipt = order.get('receipt')
                    # receipt was set to booking.id as string
                    booking = Booking.objects.filter(id=receipt).first()
                    if booking and not booking.is_paid:
                        booking.is_paid = True
                        booking.save(update_fields=["is_paid"]) 
                except Exception:
                    pass
        return JsonResponse({"success": True})
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({"success": False, "error": "Invalid signature"}, status=400)
    except Exception:
        return JsonResponse({"success": False, "error": "Unhandled error"}, status=400)


@login_required
def payment_cancel(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, rider=request.user)
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return render(request, 'riders/payment_cancelled.html', {"booking": booking})


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
    """
    Generate and return a PDF receipt for the booking.
    
    Args:
        request: The HTTP request object
        booking_id: ID of the booking to generate receipt for
        
    Returns:
        HttpResponse: PDF receipt as attachment or redirect with error message
    """
    try:
        # Get the booking or return 404
        booking = get_object_or_404(Booking, id=booking_id, rider=request.user)
        
        # Check if booking is approved
        if booking.status != 'approved':
            messages.error(request, 'Receipt is only available for approved bookings.')
            return redirect('booking_confirmation', booking_id=booking.id)
        
        # Import required libraries
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        import os
        import qrcode
        from datetime import datetime
        from decimal import Decimal, InvalidOperation
        
        # Validate dates
        if not all([hasattr(booking, 'start_date'), hasattr(booking, 'end_date')]):
            raise ValueError("Booking is missing required date information")
            
        if booking.start_date > booking.end_date:
            raise ValueError("Start date cannot be after end date")
            
        # Validate price
        try:
            total_price = Decimal(str(booking.total_price))
            if total_price < 0:
                raise ValueError("Total price cannot be negative")
        except (TypeError, InvalidOperation):
            raise ValueError("Invalid price format")
        
        # Initialize PDF buffer and canvas
        buffer = BytesIO()
        width, height = A4
        p = canvas.Canvas(buffer, pagesize=A4)

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
        
        user_logo_path = None
        if hasattr(booking.rider, 'profile_image') and booking.rider.profile_image:
            try:
                if os.path.exists(booking.rider.profile_image.path):
                    user_logo_path = booking.rider.profile_image.path
            except (ValueError, AttributeError):
                pass
                
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
        p.drawString(text_x, y - line_height, f" {booking.rider.email}")
        p.drawString(text_x, y - 2 * line_height, f" {getattr(booking.rider, 'mobile_number', '')}")
        y -= (section_gap + 2 * line_height)

        # Booking Details Section
        p.setFont(label_font, 14)
        p.setFillColor(header_color)
        p.drawString(card_x + padding, y, "Booking Details")
        y -= (line_height + 10)
        p.setFillColor(colors.white)
        p.roundRect(card_x + padding, y - 90, card_width - 2 * padding, 90, 12, fill=1, stroke=0)
        
        # Handle e-bike image
        ebike_img_path = None
        if hasattr(booking.ebike, 'image') and booking.ebike.image:
            try:
                if os.path.exists(booking.ebike.image.path):
                    ebike_img_path = booking.ebike.image.path
            except (ValueError, AttributeError):
                pass
                
        if ebike_img_path:
            p.drawImage(ebike_img_path, card_x + padding + 10, y - 80, 70, 70, mask='auto')
            
        p.setFont(label_font, 12)
        p.setFillColor(colors.black)
        p.drawString(card_x + padding + 90, y - 30, f" {booking.ebike.name}")
        p.setFont(value_font, 11)
        p.setFillColor(meta_color)
        
        # Format dates safely
        try:
            date_fmt = lambda d: d.strftime('%d %b %Y') if d else 'N/A'
            date_range = f"{date_fmt(booking.start_date)} to {date_fmt(booking.end_date)}"
        except (AttributeError, ValueError):
            date_range = "Date information not available"
            
        p.drawString(card_x + padding + 90, y - 50, f" {date_range}")
        p.setFillColor(colors.black)
        p.drawString(card_x + padding + 90, y - 70, f"RS.{total_price:.2f}")
        
        # Payment status
        p.setFillColor(status_paid_color)
        p.roundRect(card_x + card_width - 2 * padding - 70, y - 40, 50, 22, 10, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont(label_font, 11)
        p.drawCentredString(card_x + card_width - 2 * padding - 45, y - 27, " Paid")
        
        # Generate QR code
        try:
            qr_data = (
                f"BookingID:{booking.id}|User:{booking.rider.username}|"
                f"Bike:{booking.ebike.name}|From:{date_fmt(booking.start_date)}|"
                f"To:{date_fmt(booking.end_date)}|Amount:{(total_price + platform_charge):.2f}"
            )
            qr = qrcode.make(qr_data)
            qr_io = BytesIO()
            qr.save(qr_io, kind='PNG')
            qr_io.seek(0)
            qr_img = ImageReader(qr_io)
            p.drawImage(qr_img, card_x + card_width - 2 * padding - 70, y - 80, 50, 50, mask='auto')
        except Exception as e:
            # Log the error but don't fail the receipt generation
            import logging
            logging.error(f"Error generating QR code: {str(e)}")
            
        y -= (100 + section_gap)

        # Payment Section
        p.setFont(label_font, 13)
        p.setFillColor(header_color)
        p.drawString(card_x + padding, y, "Payment Received")
        y -= (line_height + 5)
        p.setFont(value_font, 11)
        p.setFillColor(colors.black)
        p.drawString(card_x + padding, y, "Rental amount")
        p.drawRightString(card_x + card_width - padding, y, f" RS.{total_price:.2f}")
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
        p.drawRightString(card_x + card_width - padding, y, f" RS.{(total_price + platform_charge):.2f}")
        y -= (section_gap)

        # Footer (inside card)
        p.setFont(value_font, 9)
        p.setFillColor(meta_color)
        p.drawCentredString(card_x + card_width / 2, card_y + 20, "AIS E-Bike Rental | GSTIN: 29ABCDE1234F1Z5 | CIN: U12345KA2023PTC123456 | Contact: support@aisebike.com")
        p.drawCentredString(card_x + card_width / 2, card_y + 8, "This is a computer-generated receipt. No signature required.")

        p.showPage()
        p.save()
        buffer.seek(0)
        
        # Set up response
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_booking_{booking.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response
        
    except Exception as e:
        # Log the error
        import logging
        logging.error(f"Error generating receipt for booking {booking_id}: {str(e)}")
        
        # Show error message to user
        messages.error(request, f"Error generating receipt: {str(e)}")
        return redirect('booking_confirmation', booking_id=booking_id)

@login_required
def view_receipt(request, booking_id):
    """
    Display a modern, clean receipt for the booking in the browser.

    Args:
        request: The HTTP request object
        booking_id: ID of the booking to display receipt for

    Returns:
        HttpResponse: Modern receipt view
    """
    try:
        booking = get_object_or_404(Booking, id=booking_id, rider=request.user)

        # Check if booking is approved or paid
        if not booking.is_paid:
            messages.warning(request, 'Receipt is only available for paid bookings.')
            return redirect('booking_confirmation', booking_id=booking.id)

        context = {
            'booking': booking,
            'site_name': 'AIS E-Bike Rental'
        }
        return render(request, 'riders/receipt.html', context)

    except Exception as e:
        import logging
        logging.error(f"Error displaying receipt for booking {booking_id}: {str(e)}")
        messages.error(request, f"Error loading receipt: {str(e)}")
        return redirect('rider_dashboard')
