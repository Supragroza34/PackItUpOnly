from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("KCLTicketingSystems", "0003_add_ticket_contact_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ticket",
            name="user",
            field=models.ForeignKey(
                settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                related_name="tickets",
                null=True,
                blank=True,
            ),
        ),
    ]

