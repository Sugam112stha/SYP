from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0004_userprofile_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellerEarning',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gross_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('commission',   models.DecimalField(decimal_places=2, max_digits=10)),
                ('net_amount',   models.DecimalField(decimal_places=2, max_digits=10)),
                ('status',       models.CharField(choices=[('pending','Pending'),('available','Available'),('paid_out','Paid Out')], default='pending', max_length=20)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('released_at',  models.DateTimeField(blank=True, null=True)),
                ('order',  models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='earning', to='myApp.order')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='earnings', to='auth.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='PayoutRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount',         models.DecimalField(decimal_places=2, max_digits=10)),
                ('method',         models.CharField(choices=[('esewa','eSewa'),('khalti','Khalti'),('bank','Bank Transfer')], max_length=20)),
                ('account_number', models.CharField(max_length=100)),
                ('status',         models.CharField(choices=[('pending','Pending'),('approved','Approved'),('paid','Paid'),('rejected','Rejected')], default='pending', max_length=20)),
                ('note',           models.TextField(blank=True)),
                ('created_at',     models.DateTimeField(auto_now_add=True)),
                ('processed_at',   models.DateTimeField(blank=True, null=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payout_requests', to='auth.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]