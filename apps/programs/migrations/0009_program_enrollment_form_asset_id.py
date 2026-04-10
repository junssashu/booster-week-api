from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0008_program_preview_assets'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='enrollment_form_asset_id',
            field=models.CharField(
                blank=True,
                help_text='Asset ID of the form shown before payment during enrollment. If set, students must fill this form before proceeding to payment.',
                max_length=50,
                null=True,
            ),
        ),
    ]
