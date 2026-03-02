from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("KCLTicketingSystems", "0002_remove_user_unique_k_number_when_not_empty_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="ticket",
            name="surname",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="ticket",
            name="k_number",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="ticket",
            name="k_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
    ]

