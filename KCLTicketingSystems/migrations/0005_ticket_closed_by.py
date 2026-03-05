from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("KCLTicketingSystems", "0004_alter_ticket_user_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="closed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="closed_tickets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
