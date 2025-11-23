# Generated migration for adding registration_fee_paid field to User model

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0018_testimonial_alter_booking_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='registration_fee_paid',
            field=models.BooleanField(default=False, help_text='One-time registration fee of ₹100 paid by vehicle providers'),
        ),
    ]
