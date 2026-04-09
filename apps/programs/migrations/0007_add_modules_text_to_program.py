from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0006_program_promotion_community'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='modules_text',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='Modules listed on the attestation PDF. Leave blank to auto-generate from degrees/steps.',
            ),
        ),
    ]
