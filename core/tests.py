from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Sum
from decimal import Decimal

from .models import EBike, Booking, Withdrawal

User = get_user_model()

class WithdrawalTestCase(TestCase):
    """
    Test cases for withdrawal functionality including minimum limits and balance calculations
    """

    def setUp(self):
        """Set up test data"""
        # Create a vehicle provider
        self.provider = User.objects.create_user(
            username='test_provider',
            email='provider@test.com',
            password='testpass123',
            is_vehicle_provider=True,
            is_verified_provider=True
        )

        # Create ebikes
        self.ebike1 = EBike.objects.create(
            name='Test EBike 1',
            description='Test description 1',
            price_per_day=500.00,
            price_per_week=3000.00,
            provider=self.provider
        )

        self.ebike2 = EBike.objects.create(
            name='Test EBike 2',
            description='Test description 2',
            price_per_day=600.00,
            price_per_week=3500.00,
            provider=self.provider
        )

        # Create a rider
        self.rider = User.objects.create_user(
            username='test_rider',
            email='rider@test.com',
            password='testpass123',
            is_rider=True
        )

        # Create approved bookings (use future dates to satisfy validation)
        import datetime
        future_start1 = datetime.date.today() + datetime.timedelta(days=1)
        future_end1 = future_start1 + datetime.timedelta(days=1)

        future_start2 = datetime.date.today() + datetime.timedelta(days=3)
        future_end2 = future_start2 + datetime.timedelta(days=1)

        self.booking1 = Booking.objects.create(
            rider=self.rider,
            ebike=self.ebike1,
            start_date=future_start1,
            end_date=future_end1,
            total_price=500.00,
            status='approved',
            is_approved=True,
            is_paid=True
        )

        self.booking2 = Booking.objects.create(
            rider=self.rider,
            ebike=self.ebike2,
            start_date=future_start2,
            end_date=future_end2,
            total_price=600.00,
            status='approved',
            is_approved=True,
            is_paid=True
        )

        self.client = Client()
        self.client.login(username='test_provider', password='testpass123')

    def test_balance_calculation_no_withdrawals(self):
        """Test balance calculation when no withdrawals have been processed"""
        # Total earnings = 500 + 600 = 1100
        # Platform charges = 1100 * 0.1 = 110
        # Available balance = 1100 - 110 = 990

        expected_balance = Decimal('990.00')

        # Test dashboard view
        response = self.client.get(reverse('vehicle_provider_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['available_balance'], expected_balance)

    def test_balance_calculation_with_withdrawals(self):
        """Test balance calculation after processing withdrawals"""
        # Create a completed withdrawal of 500
        withdrawal = Withdrawal.objects.create(
            provider=self.provider,
            amount=500.00,
            account_holder_name='Test Account',
            account_number='1234567890',
            ifsc_code='TEST0001234',
            bank_name='Test Bank',
            status='completed'
        )

        # Total earnings = 1100
        # Platform charges = 110
        # Completed withdrawals = 500
        # Available balance = 1100 - 110 - 500 = 490

        expected_balance = Decimal('490.00')

        response = self.client.get(reverse('vehicle_provider_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['available_balance'], expected_balance)

    def test_negative_balance_prevention(self):
        """Test that balance cannot go negative"""
        # Create withdrawal larger than available balance
        # Total earnings = 1100, Platform charges = 110, Available = 990
        # Withdraw 1200 (more than available)
        withdrawal = Withdrawal.objects.create(
            provider=self.provider,
            amount=1200.00,
            account_holder_name='Test Account',
            account_number='1234567890',
            ifsc_code='TEST0001234',
            bank_name='Test Bank',
            status='completed'
        )

        # Balance should be 0, not negative
        response = self.client.get(reverse('vehicle_provider_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['available_balance'], Decimal('0.00'))

    def test_minimum_withdrawal_limit(self):
        """Test that withdrawals below ₹200 are blocked"""
        # Test with amount less than 200
        response = self.client.post(reverse('request_withdrawal'), {
            'amount': '150.00',
            'account_holder_name': 'Test Account',
            'account_number': '1234567890',
            'bank_name': 'Test Bank',
            'ifsc_code': 'TEST0001234',
            'transfer_type': 'bank'
        })

        # Should redirect back with error
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('request_withdrawal'), response.url)

        # Check that message was added
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Minimum withdrawal amount is ₹200' in str(msg) for msg in messages))

        # Withdrawal should not be created
        withdrawals_count = Withdrawal.objects.filter(provider=self.provider).count()
        self.assertEqual(withdrawals_count, 0)

    def test_withdrawal_above_minimum_limit(self):
        """Test that valid withdrawals above ₹200 are allowed"""
        # Test with amount above 200
        response = self.client.post(reverse('request_withdrawal'), {
            'amount': '300.00',
            'account_holder_name': 'Test Account',
            'account_number': '1234567890',
            'bank_name': 'Test Bank',
            'ifsc_code': 'TEST0001234',
            'transfer_type': 'bank'
        })

        # Should redirect to dashboard with success
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('vehicle_provider_dashboard'), response.url)

        # Withdrawal should be created
        withdrawal = Withdrawal.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(withdrawal)
        self.assertEqual(withdrawal.amount, Decimal('300.00'))
        self.assertEqual(withdrawal.status, 'pending')

    def test_insufficient_balance_prevention(self):
        """Test that withdrawals exceeding available balance are blocked"""
        # Try to withdraw more than available balance (990)
        response = self.client.post(reverse('request_withdrawal'), {
            'amount': '1000.00',
            'account_holder_name': 'Test Account',
            'account_number': '1234567890',
            'bank_name': 'Test Bank',
            'ifsc_code': 'TEST0001234',
            'transfer_type': 'bank'
        })

        # Should redirect back with error
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('request_withdrawal'), response.url)

        # Check that insufficient balance message was added
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Insufficient balance' in str(msg) for msg in messages))

        # Withdrawal should not be created
        withdrawals_count = Withdrawal.objects.filter(provider=self.provider).count()
        self.assertEqual(withdrawals_count, 0)

    def test_withdrawal_history_view(self):
        """Test withdrawal history view"""
        # Create some withdrawals
        withdrawal1 = Withdrawal.objects.create(
            provider=self.provider,
            amount=200.00,
            account_holder_name='Test Account',
            account_number='1234567890',
            status='pending'
        )

        withdrawal2 = Withdrawal.objects.create(
            provider=self.provider,
            amount=300.00,
            account_holder_name='Test Account',
            account_number='1234567890',
            status='completed'
        )

        response = self.client.get(reverse('withdrawal_history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['withdrawals']), 2)

        # Check that withdrawals are ordered by created_at descending
        withdrawals = list(response.context['withdrawals'])
        self.assertEqual(withdrawals[0].amount, Decimal('300.00'))  # More recent
        self.assertEqual(withdrawals[1].amount, Decimal('200.00'))  # Older

    def test_receipt_download_for_completed_withdrawal(self):
        """Test that receipts can be downloaded for completed withdrawals"""
        # Create a completed withdrawal
        withdrawal = Withdrawal.objects.create(
            provider=self.provider,
            amount=250.00,
            account_holder_name='Test Account Holder',
            account_number='123456789012',
            bank_name='Test Bank',
            ifsc_code='TEST0001234',
            status='completed',
            transaction_id='TXN123456789'
        )

        # Test downloading receipt
        response = self.client.get(reverse('download_withdrawal_receipt', args=[withdrawal.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', response['Content-Disposition'])

    def test_receipt_download_denied_for_pending_withdrawal(self):
        """Test that receipts are denied for non-completed withdrawals"""
        # Create a pending withdrawal
        withdrawal = Withdrawal.objects.create(
            provider=self.provider,
            amount=250.00,
            account_holder_name='Test Account',
            account_number='1234567890',
            status='pending'
        )

        # Try to download receipt - should be denied
        response = self.client.get(reverse('download_withdrawal_receipt', args=[withdrawal.id]))
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn(reverse('withdrawal_history'), response.url)

        # Check error message
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Receipt is only available for completed withdrawals' in str(msg) for msg in messages))
