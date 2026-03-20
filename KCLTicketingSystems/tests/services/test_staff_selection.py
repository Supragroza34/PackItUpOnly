from django.test import TestCase
from KCLTicketingSystems.services import staff_selection
from KCLTicketingSystems.models import Ticket, User

class StaffSelectionTests(TestCase):

    def setUp(self):
        # Create three staff
        self.staff1 = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='testpass123',
            k_number='22222221',
            department='Informatics',    
            role=User.Role.STAFF
        )

        self.staff2 = User.objects.create_user(
            username='staff2',
            email='staff2@test.com',
            password='testpass123',
            k_number='22222222',
            department='Informatics',
            role=User.Role.STAFF
        )        
        
        self.staff3 = User.objects.create_user(
            username='staff3',
            email='staff3@test.com',
            password='testpass123',
            department='Informatics',
            k_number='22222223',
            role=User.Role.STAFF
        )

        self.staff4 = User.objects.create_user(
            username='staff4',
            email='staff4@test.com',
            password='testpass123',
            department='Medicine',
            k_number='22222223',
            role=User.Role.STAFF
        )

        self.staff5 = User.objects.create_user(
            username='staff5',
            email='staff5@test.com',
            password='testpass123',
            department='Engineering',
            k_number='22222223',
            role=User.Role.STAFF
        )                

        # Create test user for ticket
        self.ticket_user = User.objects.create_user(
            username='ticketuser',
            email='ticketuser@test.com',
            password='testpass123',
            first_name='Jame',
            last_name='Does',
            k_number='12345679',
            role=User.Role.STUDENT
        )  

        # Create test ticket
        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help with software',
            assigned_to=self.staff1,
            status=Ticket.Status.PENDING
        )

        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help with software again',
            assigned_to=self.staff1,
            status=Ticket.Status.PENDING
        )

        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help with software still',
            assigned_to=self.staff1,
            status=Ticket.Status.PENDING
        )

        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help with software',
            assigned_to=self.staff2,
            status=Ticket.Status.PENDING
        )

        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help with software',
            assigned_to=self.staff2,
            status=Ticket.Status.PENDING
        )

        self.ticket_data = {
            'user': self.ticket_user,
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python'
        }                        

    def test_correct_number_of_tickets_returned_for_staff(self):
        staff_1_tickets = staff_selection.get_number_of_tickets_assigned_to_staff(self.staff1.id)
        staff_2_tickets = staff_selection.get_number_of_tickets_assigned_to_staff(self.staff2.id)
        staff_3_tickets = staff_selection.get_number_of_tickets_assigned_to_staff(self.staff3.id)
        self.assertEqual(staff_1_tickets, 3)
        self.assertEqual(staff_2_tickets, 2)
        self.assertEqual(staff_3_tickets, 0)

    def test_only_staff_in_department_returned(self):
        department = self.ticket_data.get("department")
        staff_members = staff_selection.get_staff_from_department(department)
        staff_member_departments = []
        for member in staff_members:
            staff_member_departments.append(member["department"])
        medicine_present = "Medicine" in staff_member_departments
        engineering_present = "Engineering" in staff_member_departments    
        self.assertEqual(medicine_present, False)
        self.assertEqual(engineering_present, False)      

    def test_correct_staff_member_returned(self):
        department = self.ticket_data.get("department")
        staff_member = staff_selection.get_staff_with_least_tickets_in_department(department)
        self.assertEqual(staff_member["id"], self.staff3.id)

    def test_ticket_can_be_created(self):
        department = 'Informatics'
        assigned_to_id = staff_selection.get_staff_with_least_tickets_in_department(department)["id"]
        assigned_to = User.objects.get(id=assigned_to_id)
        new_ticket_data = {
            'user': self.ticket_user,
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python',
            'assigned_to': assigned_to
        }
        count_before = Ticket.objects.count()
        Ticket.objects.create(**new_ticket_data)
        count_after = Ticket.objects.count()
        self.assertEqual(count_before, count_after-1)
