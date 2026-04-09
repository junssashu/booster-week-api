from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0005_program_installment_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='whatsapp_community_url',
            field=models.TextField(blank=True, null=True, help_text='WhatsApp community link for enrolled students of this program'),
        ),
        migrations.AddField(
            model_name='program',
            name='promotion_details',
            field=models.TextField(blank=True, null=True, help_text='Rich text description shown below degree list on mobile'),
        ),
    ]
