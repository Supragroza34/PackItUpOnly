# Generated migration to remove unique constraint from k_number

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('KCLTicketingSystems', '0002_rename_issues_additional_details_and_add_type_of_issue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='k_number',
            field=models.CharField(max_length=255),
        ),
    ]
