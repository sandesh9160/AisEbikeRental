<<<<<<< HEAD
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
import time


class Command(BaseCommand):
    help = 'Test email configuration and send test emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Test email address to send to',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all email configurations',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Email Configuration Test ===\n')
        )

        # Display current email configuration
        self.stdout.write('Email Backend: ' + settings.EMAIL_BACKEND)
        self.stdout.write('Default From Email: ' + settings.DEFAULT_FROM_EMAIL or 'None')
        self.stdout.write('Contact Receiver Email: ' + getattr(settings, 'CONTACT_RECEIVER_EMAIL', 'None'))
        self.stdout.write('Server Email: ' + getattr(settings, 'SERVER_EMAIL', 'None'))
        self.stdout.write('')

        test_email = options.get('email') or getattr(settings, 'CONTACT_RECEIVER_EMAIL', None)

        if not test_email:
            raise CommandError('No test email provided. Use --email or set CONTACT_RECEIVER_EMAIL in settings.')

        # Test individual email
        self.stdout.write(f'Sending test email to: {test_email}')
        try:
            start_time = time.time()
            send_mail(
                subject='Test Email - AIS E-bike Rental',
                message=f"""This is a test email sent from AIS E-bike Rental system.

Server time: {time.strftime('%Y-%m-%d %H:%M:%S')}
Backend: {settings.EMAIL_BACKEND}

If you received this email, the email configuration is working correctly!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            end_time = time.time()

            self.stdout.write(
                self.style.SUCCESS(f'✓ Test email sent successfully in {end_time - start_time:.2f} seconds')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to send test email: {str(e)}')
            )
            return

        # Test multiple emails if requested
        if options.get('all'):
            self.stdout.write('\nTesting multiple email addresses...')
            emails = [
                # Add more test emails here if needed
                (test_email, 'Copy of test email')
            ]

            try:
                messages = [('Test Email Batch', f'This is email {i+1}', settings.DEFAULT_FROM_EMAIL, [email])
                           for i, (email, desc) in enumerate(emails)]

                send_mass_mail(
                    datatuple=messages,
                    fail_silently=False
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ Mass email test successful')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Mass email test failed: {str(e)}')
                )

        # Test contact form email if admin email is available
        admin_email = getattr(settings, 'CONTACT_RECEIVER_EMAIL', None)
        if admin_email and admin_email != test_email:
            self.stdout.write(f'\nTesting admin notification email to: {admin_email}')
            try:
                send_mail(
                    subject='[Contact Form Test] System Test',
                    message="""This is a test of the admin notification system
for the contact form on AIS E-bike Rental.

If you received this email, the contact form email notifications are working correctly.

Test performed by: Django management command
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ Admin notification email test successful')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Admin notification email test failed: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('\n=== Email Configuration Test Complete ===')
        )
=======
"""
Test email functionality for debugging production email issues.
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email configuration and send a test email'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Testing Email Configuration...\n')

        # Check DEBUG setting
        debug_mode = getattr(settings, 'DEBUG', True)
        self.stdout.write(f'DEBUG mode: {debug_mode}')

        # Check email backend
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        self.stdout.write(f'Email backend: {email_backend}')

        # Check email settings
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'NOT SET')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')
        smtp_host = getattr(settings, 'EMAIL_HOST', 'NOT SET')
        smtp_port = getattr(settings, 'EMAIL_PORT', 'NOT SET')
        smtp_user = getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')

        self.stdout.write(f'Admin email: {admin_email}')
        self.stdout.write(f'From email: {from_email}')
        self.stdout.write(f'SMTP host: {smtp_host}')
        self.stdout.write(f'SMTP port: {smtp_port}')
        self.stdout.write(f'SMTP user: {"SET" if smtp_user != "NOT SET" else "NOT SET"}')

        # Test email connection
        try:
            self.stdout.write('\n📧 Testing email connection...')
            connection = get_connection()
            connection.open()
            connection.close()
            self.stdout.write(self.style.SUCCESS('✓ Email connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Email connection failed: {str(e)}'))
            return

        # Send test email
        if admin_email != 'NOT SET':
            try:
                self.stdout.write('\n📨 Sending test email...')
                subject = 'Test Email - AIS E-Bike Rental System'
                message = '''
This is a test email to verify the email configuration is working properly.

If you received this email, it means:
- Email backend is configured correctly
- SMTP settings are working
- Django can send emails successfully

All admin notifications should now work in production!
                '''

                result = send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[admin_email],
                    fail_silently=False
                )

                if result == 1:
                    self.stdout.write(self.style.SUCCESS(f'✓ Test email sent successfully to {admin_email}'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ Email sending returned: {result}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to send test email: {str(e)}'))
                logger.error(f'Test email failed: {str(e)}')
        else:
            self.stdout.write(self.style.WARNING('⚠ ADMIN_EMAIL not configured - cannot test email sending'))

        self.stdout.write('\n🎉 Email configuration test completed!')
>>>>>>> bc478c3b2f51a242be15138610bac84cb0a5f46a
