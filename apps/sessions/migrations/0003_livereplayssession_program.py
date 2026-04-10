import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('live_sessions', '0002_sessionattendance'),
        ('programs', '0009_program_enrollment_form_asset_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='livereplayssession',
            name='program',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sessions',
                to='programs.program',
            ),
        ),
    ]
