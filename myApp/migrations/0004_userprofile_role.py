from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0003_remove_order_buyer_name_remove_order_buyer_phone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                choices=[('buyer', 'Buyer'), ('seller', 'Seller')],
                default='buyer',
                max_length=10,
            ),
        ),
    ]