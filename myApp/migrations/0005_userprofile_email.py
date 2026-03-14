from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0004_userprofile_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='email_token',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]