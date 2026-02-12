# Generated migration to remove unique constraint from k_number

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Updated to match the actual name of the previous migration
        ('KCLTicketingSystems', '0002_attachment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='k_number',
            field=models.CharField(max_length=255),
        ),
    ]
