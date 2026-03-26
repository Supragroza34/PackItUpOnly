from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ...models import Ticket

class Command(BaseCommand):
    help = 'Delete tickets that have been closed for more than 24 hours.'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=24)
        to_delete = Ticket.objects.filter(status=Ticket.Status.CLOSED, updated_at__lte=cutoff)
        count = to_delete.count()
        to_delete.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} closed tickets older than 24 hours.'))
