from django.core.management.base import BaseCommand
from core.models import Booking, EBike, User
from django.db import models
from decimal import Decimal


class Command(BaseCommand):
    help = 'Debug provider earnings calculations'

    def handle(self, *args, **options):
        # Get all vehicle providers
        providers = User.objects.filter(is_vehicle_provider=True)

        self.stdout.write('=== PROVIDER EARNINGS DEBUG ===\n')

        for provider in providers:
            self.stdout.write(f'Provider: {provider.username} (ID: {provider.id})')

            # Get all bookings for this provider's ebikes
            ebikes = EBike.objects.filter(provider=provider)
            ebike_ids = ebikes.values_list('id', flat=True)

            # All bookings for this provider
            all_bookings = Booking.objects.filter(ebike__provider=provider)

            # Approved bookings for dashboard calculation
            approved_bookings = Booking.objects.filter(
                ebike__provider=provider,
                is_approved=True
            )

            self.stdout.write(f'  Total ebikes: {ebikes.count()}')
            self.stdout.write(f'  Total bookings: {all_bookings.count()}')
            self.stdout.write(f'  Approved bookings: {approved_bookings.count()}')

            # Calculate earnings like dashboard does
            total_earnings = sum(float(booking.total_price) for booking in approved_bookings)
            platform_charges = Decimal(str(total_earnings)) * Decimal('0.1')
            available_balance = Decimal(str(total_earnings)) - platform_charges

            # Also calculate balance considering withdrawals
            from core.models import Withdrawal
            completed_withdrawals = Withdrawal.objects.filter(
                provider=provider,
                status__in=['approved', 'completed']
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.0')

            available_balance_with_withdrawals = available_balance - completed_withdrawals
            available_balance_with_withdrawals = max(available_balance_with_withdrawals, Decimal('0.0'))

            self.stdout.write(f'  Total earnings (approved): ₹{total_earnings}')
            self.stdout.write(f'  Platform charges: ₹{platform_charges}')
            self.stdout.write(f'  Available balance: ₹{available_balance}')
            self.stdout.write(f'  After withdrawals: ₹{available_balance_with_withdrawals}')

            # Show details of approved bookings
            if approved_bookings.exists():
                self.stdout.write('  Approved bookings details:')
                for booking in approved_bookings:
                    self.stdout.write(f'    ID: {booking.id}, Amount: ₹{booking.total_price}, Rider: {booking.rider.username}, Date: {booking.start_date}')
            else:
                self.stdout.write('  No approved bookings found.')

            # Show pending approvals
            pending_bookings = all_bookings.filter(is_approved=False, is_rejected=False)
            if pending_bookings.exists():
                self.stdout.write(f'  Pending bookings: {pending_bookings.count()}')
                for booking in pending_bookings:
                    self.stdout.write(f'    ID: {booking.id}, Amount: ₹{booking.total_price}, Rider: {booking.rider.username}, Paid: {booking.is_paid}')
            else:
                self.stdout.write('  No pending bookings.')

            self.stdout.write('\n')  # Empty line between providers

        # Summary stats
        total_approved = Booking.objects.filter(is_approved=True).count()
        total_pending = Booking.objects.filter(is_approved=False, is_rejected=False).count()
        total_bookings = Booking.objects.all().count()

        self.stdout.write('=== SUMMARY ===')
        self.stdout.write(f'Total bookings: {total_bookings}')
        self.stdout.write(f'Approved bookings: {total_approved}')
        self.stdout.write(f'Pending bookings: {total_pending}')
