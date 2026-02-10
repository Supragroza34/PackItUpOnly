# Generated migration to fix database schema

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('KCLTicketingSystems', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ticket',
            old_name='issues',
            new_name='additional_details',
        ),
        migrations.AddField(
            model_name='ticket',
            name='type_of_issue',
            field=models.CharField(default='', max_length=255),
        ),
    ]

