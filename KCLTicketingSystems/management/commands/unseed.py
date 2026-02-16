from django.core.management.base import BaseCommand
from ...models import User, Ticket, Attachment, Reply

class Command(BaseCommand):

    def handle(self, *args, **options):

        User.objects.all().delete()
        Ticket.objects.all().delete()
        Reply.objects.all().delete()
        Attachment.objects.all().delete()

