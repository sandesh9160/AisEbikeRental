# PythonAnywhere Deployment - E-Bike Availability Updates

## Management Command Details

The `update_ebike_availability` command:
- Finds approved bookings where e-bikes are currently unavailable
- Checks if the booking end date/time has passed
- Automatically marks e-bikes as available when bookings expire
- Provides detailed logging of all changes made

## Cron Job Setup on PythonAnywhere

### Option 1: Use the Provided Script (Recommended)
1. Upload the `pythonanywhere_cron_setup.sh` file to your project directory
2. Make it executable: `chmod +x pythonanywhere_cron_setup.sh`
3. In PythonAnywhere dashboard → Tasks → Add a new scheduled task:
   - **Command:** `/home/yourusername/AisEbikeRental/pythonanywhere_cron_setup.sh`
   - **Schedule:** Every hour (or based on your needs)

### Option 2: Direct Command (Simpler)
1. In PythonAnywhere dashboard → Tasks → Add a new scheduled task:
   - **Command:** `cd /home/yourusername/AisEbikeRental && python manage.py update_ebike_availability`
   - **Schedule:** Every hour

## Environment Setup Requirements

Make sure your PythonAnywhere environment has:
- `DJANGO_SETTINGS_MODULE=ais_ebike_rental.settings`
- Python path including your project directory
- Virtual environment activated (if using one)

## Testing the Command

You can test the command manually in the PythonAnywhere console:

```bash
cd /home/yourusername/AisEbikeRental
python manage.py update_ebike_availability --verbosity=2
```

The `--verbosity=2` flag will show more detailed output.

## Frequency Recommendations

Common schedules:
- **Every hour**: `0 * * * *`
- **Every 30 minutes**: `*/30 * * * *`
- **Every 15 minutes**: `*/15 * * * *`

Choose based on your business needs. More frequent checks ensure e-bikes become available promptly after bookings end.

## Troubleshooting

If the command fails:
1. Check Django settings are properly loaded
2. Ensure database is accessible
3. Check timezone settings match your deployment
4. Review command output for error messages

## Email Configuration for Admin Notifications

**Required Environment Variables in PythonAnywhere:**

1. Go to your PythonAnywhere dashboard
2. Go to "Variables" section under your web app
3. Add these environment variables:

```
DEBUG=False
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ebikerental19@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=AIS E-Bike Rental <ebikerental19@gmail.com>
ADMIN_EMAIL=ebikerental19@gmail.com
```

**Important:**
- Get the Gmail app password from Google Account settings
- The Gmail account should have 2-factor authentication enabled
- Use the app-specific password, not your regular password

## Testing Email in Production

After setting environment variables, use the test command:

```bash
cd /home/yourusername/AisEbikeRental
python manage.py test_email
```

This will:
- Check if DEBUG=False
- Test SMTP connection
- Send a test email to verify configuration

## Troubleshooting Email Issues

If no emails are received:
1. Check PythonAnywhere error logs for SMTP errors
2. Verify environment variables are set correctly
3. Test Gmail SMTP manually if needed
4. Check if Gmail is blocking the sender

## Production Best Practices

- Monitor the command outputs through PythonAnywhere task logs
- Set up email notifications if needed for failed commands
- Consider logging command results to a file for audit purposes
- Test with verbosity levels to ensure proper operation

## Admin Email Notifications (Now Working)

When these environment variables are set, the system will send admin emails for:
- 🛵 **Booking requests** - When riders book e-bikes
- 📋 **Document verification** - When providers upload documents
- 💰 **Withdrawal requests** - When providers request payouts
