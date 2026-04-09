from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_appsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='appsettings',
            name='payment_expiry_minutes',
            field=models.IntegerField(default=15, help_text='Minutes before a pending payment expires'),
        ),
    ]
