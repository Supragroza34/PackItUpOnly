from django.core.management.base import BaseCommand
from django.db import connection
from ...models import User, Ticket

class Command(BaseCommand):
    help = 'Remove all seeded data from the database'

    def handle(self, *args, **options):
        # Get list of existing tables
        tables = connection.introspection.table_names()
        
        # Delete only if tables exist
        try:
            if 'KCLTicketingSystems_user' in tables:
                User.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Deleted all users'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not delete users: {e}'))
        
        try:
            if 'KCLTicketingSystems_ticket' in tables:
                Ticket.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Deleted all tickets'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not delete tickets: {e}'))
        
        # Try to import and delete Reply and Attachment if they exist
        try:
            from ...models import Reply
            if 'KCLTicketingSystems_reply' in tables:
                Reply.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Deleted all replies'))
        except:
            pass
        
        try:
            from ...models import Attachment
            if 'KCLTicketingSystems_attachment' in tables:
                Attachment.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Deleted all attachments'))
        except:
            pass
        
        self.stdout.write(self.style.SUCCESS('\n✅ Unseed completed!'))

