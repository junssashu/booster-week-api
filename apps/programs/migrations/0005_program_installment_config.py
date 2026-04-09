from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0004_alter_asset_type_alter_degreefile_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='num_installments',
            field=models.IntegerField(default=2, help_text='Number of installment payments'),
        ),
        migrations.AddField(
            model_name='program',
            name='degrees_per_installment',
            field=models.JSONField(blank=True, null=True, help_text='Array mapping each installment to number of degrees unlocked.'),
        ),
        migrations.AddField(
            model_name='program',
            name='completion_threshold',
            field=models.IntegerField(default=70, help_text='Min avg completion % to unlock next degree'),
        ),
    ]
