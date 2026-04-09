from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0007_add_modules_text_to_program'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='preview_assets',
            field=models.JSONField(
                blank=True,
                null=True,
                help_text='List of teaser videos/audios shown on programme detail page. Format: [{type, title, description, url}]',
            ),
        ),
    ]
