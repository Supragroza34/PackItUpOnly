from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from ..models import Ticket, User

class DeleteOldClosedTicketsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            k_number='12345678',
            role=User.Role.STUDENT
        )
        now = timezone.now()
        # Ticket closed 25 hours ago (should be deleted)
        self.old_ticket = Ticket.objects.create(
            user=self.user,
            department='Informatics',
            type_of_issue='Old Issue',
            additional_details='Old closed ticket',
            status=Ticket.Status.CLOSED,
            updated_at=now - timedelta(hours=25)
        )
        # Ticket closed 23 hours ago (should NOT be deleted)
        self.recent_ticket = Ticket.objects.create(
            user=self.user,
            department='Informatics',
            type_of_issue='Recent Issue',
            additional_details='Recent closed ticket',
            status=Ticket.Status.CLOSED,
            updated_at=now - timedelta(hours=23)
        )
        # Ticket not closed (should NOT be deleted)
        self.open_ticket = Ticket.objects.create(
            user=self.user,
            department='Informatics',
            type_of_issue='Open Issue',
            additional_details='Open ticket',
            status=Ticket.Status.PENDING,
            updated_at=now - timedelta(hours=30)
        )

    def test_delete_old_closed_tickets_command(self):
        call_command('delete_old_closed_tickets')
        tickets = Ticket.objects.all()
        types = set(t.type_of_issue for t in tickets)
        self.assertNotIn('Old Issue', types)
        self.assertIn('Recent Issue', types)
        self.assertIn('Open Issue', types)
        self.assertEqual(tickets.count(), 2)
