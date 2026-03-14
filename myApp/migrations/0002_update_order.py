# Generated for Alpha Mart — adds payment fields to Order model
# Place this file at:  myApp/migrations/0002_update_order_payment_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0001_initial'),
    ]

    operations = [

        # --- Amount fields ---
        migrations.AddField(
            model_name='order',
            name='shipping_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='discount_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),

        # --- Payment method ---
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                blank=True,
                max_length=20,
                choices=[
                    ('esewa',  'eSewa'),
                    ('khalti', 'Khalti'),
                    ('card',   'Card (Simulated)'),
                    ('cod',    'Cash on Delivery'),
                ],
            ),
        ),

        # --- Payment status ---
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                default='unpaid',
                max_length=20,
                choices=[
                    ('unpaid',   'Unpaid'),
                    ('pending',  'Pending Verification'),
                    ('verified', 'Verified'),
                    ('failed',   'Failed'),
                ],
            ),
        ),

        # --- Transaction IDs ---
        migrations.AddField(
            model_name='order',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_ref_id',
            field=models.CharField(blank=True, max_length=200),
        ),

        # --- Timestamps ---
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # --- Buyer contact ---
        migrations.AddField(
            model_name='order',
            name='buyer_phone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='buyer_name',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]