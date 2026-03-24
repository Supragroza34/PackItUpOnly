from django.core.management.base import BaseCommand
from django.db import connection
from ...models import User, Ticket

class Command(BaseCommand):
    """Expose the unseed command so operational tasks stay repeatable and auditable."""
    help = 'Remove all seeded data from the database'

    def _delete_model(self, model_class, table_name, model_name, tables):
        """Delete all records from a model if table exists. This keeps operational tasks repeatable and auditable."""
        if table_name in tables:
            try:
                model_class.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted all {model_name}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not delete {model_name}: {e}'))

    def _delete_optional_models(self, tables):
        """Delete Reply and Attachment models if they exist. This keeps operational tasks repeatable and auditable."""
        try:
            from ...models import Reply
            self._delete_model(Reply, 'KCLTicketingSystems_reply', 'replies', tables)
        except:
            pass
        try:
            from ...models import Attachment
            self._delete_model(Attachment, 'KCLTicketingSystems_attachment', 'attachments', tables)
        except:
            pass

    def handle(self, *args, **options):
        """Run the command's primary workflow so operational tasks stay repeatable and auditable."""
        tables = connection.introspection.table_names()
        self._delete_model(User, 'KCLTicketingSystems_user', 'users', tables)
        self._delete_model(Ticket, 'KCLTicketingSystems_ticket', 'tickets', tables)
        self._delete_optional_models(tables)
        self.stdout.write(self.style.SUCCESS('\n✅ Unseed completed!'))

