import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactSubmission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True, max_length=255)),
                ('message', models.TextField()),
                ('type', models.CharField(
                    choices=[('contact', 'Contact'), ('bug', 'Bug Report')],
                    default='contact',
                    max_length=10,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'contact_submissions',
                'ordering': ['-created_at'],
            },
        ),
    ]
