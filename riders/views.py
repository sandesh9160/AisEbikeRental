from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import Booking, EBike
from .forms import BookingForm
from django.contrib import messages
def rider_dashboard(request):
    bookings = Booking.objects.filter(rider=request.user)  # Get bookings for the current rider
    booked_ebikes = [booking.ebike for booking in bookings if booking.is_approved]  # List of booked e-bikes

    available_ebikes = EBike.objects.all()  # All available e-bikes

    return render(request, 'riders/dashboard.html', {
        'bookings': bookings,
        'available_ebikes': available_ebikes,
        'booked_ebikes': booked_ebikes, 
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

            # Create booking instance but don't save yet
            booking = form.save(commit=False)
            booking.total_price = total_price
            booking.ebike = ebike
            booking.rider = request.user  # Set the rider to the currently logged-in user
            booking.save()

            return redirect('rider_dashboard')
    else:
        form = BookingForm()

    return render(request, 'riders/book_bike.html', {'form': form, 'ebike': ebike})
def booking_confirmation(request):
    return render(request, 'riders/booking_confirmation.html')

