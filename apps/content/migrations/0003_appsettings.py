from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_contactsubmission'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppSettings',
            fields=[
                ('id', models.IntegerField(default=1, primary_key=True, serialize=False)),
                ('background_music_url', models.URLField(blank=True, default='', max_length=500)),
                ('app_name', models.CharField(default='Booster Week', max_length=100)),
                ('social_links', models.JSONField(blank=True, default=dict)),
                ('footer_tagline', models.TextField(default='Elevez vos vibrations et transformez votre quotidien.')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'app_settings',
                'verbose_name_plural': 'App Settings',
            },
        ),
    ]
