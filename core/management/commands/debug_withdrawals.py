from django.core.management.base import BaseCommand
from core.models import Withdrawal, User


class Command(BaseCommand):
    help = 'Debug withdrawal requests and statuses'

    def handle(self, *args, **options):
        # Show all withdrawals
        withdrawals = Withdrawal.objects.all().select_related('provider', 'processed_by').order_by('-created_at')

        self.stdout.write('=== ALL WITHDRAWALS DEBUG ===\n')

        for withdrawal in withdrawals:
            status_badge = {
                'pending': 'PENDING',
                'approved': 'APPROVED',
                'rejected': 'REJECTED',
                'completed': 'COMPLETED'
            }.get(withdrawal.status, 'UNKNOWN')

            self.stdout.write(f'ID: {withdrawal.id}')
            self.stdout.write(f'  Provider: {withdrawal.provider.username} (ID: {withdrawal.provider.id})')
            self.stdout.write(f'  Amount: ₹{withdrawal.amount}')
            self.stdout.write(f'  Status: {status_badge}')
            self.stdout.write(f'  Bank: {withdrawal.account_holder_name} - {withdrawal.bank_name} - {withdrawal.account_number} - {withdrawal.ifsc_code}')
            self.stdout.write(f'  UPI: {withdrawal.upi_id or "N/A"}')
            self.stdout.write(f'  Created: {withdrawal.created_at}')
            self.stdout.write(f'  Processed By: {withdrawal.processed_by.username if withdrawal.processed_by else "N/A"}')
            self.stdout.write(f'  Processed At: {withdrawal.processed_at or "N/A"}')
            self.stdout.write(f'  Transaction ID: {withdrawal.transaction_id or "N/A"}')
            self.stdout.write('')

        # Group by provider and status
        self.stdout.write('=== SUMMARY BY PROVIDER ===\n')

        providers = User.objects.filter(is_vehicle_provider=True)
        total_completed_amount = 0

        for provider in providers:
            provider_withdrawals = withdrawals.filter(provider=provider)

            self.stdout.write(f'Provider: {provider.username}')

            pending = provider_withdrawals.filter(status='pending')
            approved = provider_withdrawals.filter(status='approved')
            rejected = provider_withdrawals.filter(status='rejected')
            completed = provider_withdrawals.filter(status='completed')

            self.stdout.write(f'  Pending: {pending.count()} requests')
            if pending.exists():
                total_pending = sum(w.amount for w in pending)
                self.stdout.write(f'    Total pending amount: ₹{total_pending}')

            self.stdout.write(f'  Approved: {approved.count()} requests')
            if approved.exists():
                total_approved = sum(w.amount for w in approved)
                self.stdout.write(f'    Total approved amount: ₹{total_approved}')

            self.stdout.write(f'  Completed: {completed.count()} requests')
            if completed.exists():
                total_comp = sum(w.amount for w in completed)
                self.stdout.write(f'    Total completed amount: ₹{total_comp}')
                total_completed_amount += total_comp

            self.stdout.write('')

        self.stdout.write(f'Total completed withdrawals across all providers: ₹{total_completed_amount}')
