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
