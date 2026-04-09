from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('enrollments', '0003_add_payment_url')]
    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='installment_config_snapshot',
            field=models.JSONField(default=dict, blank=True),
        ),
    ]
