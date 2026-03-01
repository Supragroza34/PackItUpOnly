from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from KCLTicketingSystems.models import Ticket, Reply, User

class ReplyCreateViewTests(APITestCase):

    def setUp(self):
        # Create users
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STAFF
        )
        
        # Create test user for ticket
        self.ticket_user = User.objects.create_user(
            username='ticketuser',
            email='ticketuser@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            k_number='12345678',
            role=User.Role.STUDENT
        )

        # Create test ticket
        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help with software',
            status=Ticket.Status.PENDING
        )

        self.url = f'/api/replies/create/'

    def test_authenticated_user_can_post_reply(self):
        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": self.ticket.id,
            "body": "This is a test reply",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        created_reply = Reply.objects.get(ticket=self.ticket)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_before, count_after-1)
        self.assertEqual(created_reply.body, "This is a test reply")

    def test_unauthenticated_user_cannot_post_reply(self):
        data = {
            "user": self.ticket_user.id,
            "ticket": self.ticket.id,
            "body": "Unauthorized comment",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(count_after, count_before)        

    def test_reply_is_linked_to_logged_in_staff(self):

        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": self.ticket.id,
            "body": "User link test"
        }

        self.client.post(self.url, data)

        reply = Reply.objects.first()
        self.assertEqual(reply.user, self.staff)

    def test_invalid_reply_post_no_body(self):
        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": self.ticket.id,
            "body": "",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(count_before, count_after)

    def test_invalid_reply_post_no_ticket(self):
        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": "",
            "body": "Body present",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(count_before, count_after)          