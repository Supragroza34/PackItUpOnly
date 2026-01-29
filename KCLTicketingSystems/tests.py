from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Ticket
from datetime import datetime


class TicketModelTest(TestCase):
    """Test cases for the Ticket model"""

    def setUp(self):
        """Set up test data"""
        self.ticket_data = {
            'name': 'John',
            'surname': 'Doe',
            'k_number': '12345678',
            'k_email': '12345678@kcl.ac.uk',
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python'
        }

    def test_ticket_creation(self):
        """Test creating a ticket"""
        ticket = Ticket.objects.create(**self.ticket_data)
        self.assertEqual(ticket.name, 'John')
        self.assertEqual(ticket.surname, 'Doe')
        self.assertEqual(ticket.k_number, '12345678')
        self.assertEqual(ticket.k_email, '12345678@kcl.ac.uk')
        self.assertEqual(ticket.department, 'Informatics')
        self.assertEqual(ticket.type_of_issue, 'Software Installation Issues')
        self.assertEqual(ticket.additional_details, 'Need help installing Python')
        self.assertIsNotNone(ticket.created_at)
        self.assertIsNotNone(ticket.updated_at)

    def test_ticket_str_method(self):
        """Test the __str__ method of Ticket model"""
        ticket = Ticket.objects.create(**self.ticket_data)
        expected_str = f"{ticket.name} {ticket.surname}  - {ticket.k_number}"
        self.assertEqual(str(ticket), expected_str)

    def test_ticket_k_number_unique(self):
        """Test that K-Number must be unique"""
        Ticket.objects.create(**self.ticket_data)
        with self.assertRaises(Exception):
            Ticket.objects.create(**self.ticket_data)

    def test_ticket_auto_timestamps(self):
        """Test that created_at and updated_at are automatically set"""
        ticket = Ticket.objects.create(**self.ticket_data)
        self.assertIsNotNone(ticket.created_at)
        self.assertIsNotNone(ticket.updated_at)
        self.assertIsInstance(ticket.created_at, datetime)
        self.assertIsInstance(ticket.updated_at, datetime)


class TicketAPITest(TestCase):
    """Test cases for the Ticket API endpoint"""

    def setUp(self):
        """Set up test client and valid data"""
        self.client = APIClient()
        self.url = '/api/submit-ticket/'
        self.valid_data = {
            'name': 'John',
            'surname': 'Doe',
            'k_number': '12345678',
            'k_email': '12345678@kcl.ac.uk',
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python'
        }

    def test_submit_ticket_success(self):
        """Test successful ticket submission"""
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('ticket_id', response.data)
        self.assertEqual(response.data['message'], 'Ticket submitted successfully')
        
        # Verify ticket was created in database
        ticket = Ticket.objects.get(k_number='12345678')
        self.assertEqual(ticket.name, 'John')
        self.assertEqual(ticket.surname, 'Doe')

    def test_submit_ticket_missing_name(self):
        """Test submission with missing name"""
        data = self.valid_data.copy()
        data.pop('name')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('name', response.data['errors'])

    def test_submit_ticket_missing_surname(self):
        """Test submission with missing surname"""
        data = self.valid_data.copy()
        data.pop('surname')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('surname', response.data['errors'])

    def test_submit_ticket_missing_k_number(self):
        """Test submission with missing K-Number"""
        data = self.valid_data.copy()
        data.pop('k_number')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('k_number', response.data['errors'])

    def test_submit_ticket_missing_email(self):
        """Test submission with missing email"""
        data = self.valid_data.copy()
        data.pop('k_email')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('k_email', response.data['errors'])

    def test_submit_ticket_missing_department(self):
        """Test submission with missing department"""
        data = self.valid_data.copy()
        data.pop('department')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('department', response.data['errors'])

    def test_submit_ticket_missing_type_of_issue(self):
        """Test submission with missing type of issue"""
        data = self.valid_data.copy()
        data.pop('type_of_issue')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('type_of_issue', response.data['errors'])

    def test_submit_ticket_missing_additional_details(self):
        """Test submission with missing additional details"""
        data = self.valid_data.copy()
        data.pop('additional_details')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('additional_details', response.data['errors'])

    def test_submit_ticket_name_with_numbers(self):
        """Test submission with name containing numbers"""
        data = self.valid_data.copy()
        data['name'] = 'John123'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('name', response.data['errors'])
        self.assertEqual(response.data['errors']['name'], 'Name cannot contain numbers')

    def test_submit_ticket_surname_with_numbers(self):
        """Test submission with surname containing numbers"""
        data = self.valid_data.copy()
        data['surname'] = 'Doe456'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('surname', response.data['errors'])
        self.assertEqual(response.data['errors']['surname'], 'Surname cannot contain numbers')

    def test_submit_ticket_k_number_with_letters(self):
        """Test submission with K-Number containing letters"""
        data = self.valid_data.copy()
        data['k_number'] = '12345abc'
        data['k_email'] = '12345abc@kcl.ac.uk'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('k_number', response.data['errors'])
        self.assertEqual(response.data['errors']['k_number'], 'K-Number cannot contain letters')

    def test_submit_ticket_invalid_email_format(self):
        """Test submission with invalid email format"""
        data = self.valid_data.copy()
        data['k_email'] = 'wrong@email.com'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('k_email', response.data['errors'])
        self.assertIn('KNumber@kcl.ac.uk', response.data['errors']['k_email'])

    def test_submit_ticket_email_not_matching_k_number(self):
        """Test submission with email not matching K-Number"""
        data = self.valid_data.copy()
        data['k_number'] = '12345678'
        data['k_email'] = '87654321@kcl.ac.uk'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('k_email', response.data['errors'])

    def test_submit_ticket_invalid_department(self):
        """Test submission with invalid department"""
        data = self.valid_data.copy()
        data['department'] = 'InvalidDepartment'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('department', response.data['errors'])
        self.assertEqual(response.data['errors']['department'], 'Invalid department selected')

    def test_submit_ticket_valid_departments(self):
        """Test submission with all valid departments"""
        valid_departments = ['Informatics', 'Engineering', 'Medicine']
        for dept in valid_departments:
            data = self.valid_data.copy()
            data['department'] = dept
            data['k_number'] = f'1234567{valid_departments.index(dept)}'
            data['k_email'] = f'1234567{valid_departments.index(dept)}@kcl.ac.uk'
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, 
                           f"Failed for department: {dept}")

    def test_submit_ticket_duplicate_k_number(self):
        """Test submission with duplicate K-Number"""
        # Create first ticket
        response1 = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Try to create second ticket with same K-Number
        data = self.valid_data.copy()
        data['name'] = 'Jane'  # Different name
        response2 = self.client.post(self.url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response2.data)
        self.assertIn('k_number', response2.data['errors'])
        self.assertIn('already exists', response2.data['errors']['k_number'])

    def test_submit_ticket_empty_string_fields(self):
        """Test submission with empty string fields"""
        data = {
            'name': '',
            'surname': '',
            'k_number': '',
            'k_email': '',
            'department': '',
            'type_of_issue': '',
            'additional_details': ''
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        # All fields should have errors
        self.assertIn('name', response.data['errors'])
        self.assertIn('surname', response.data['errors'])
        self.assertIn('k_number', response.data['errors'])
        self.assertIn('k_email', response.data['errors'])
        self.assertIn('department', response.data['errors'])
        self.assertIn('type_of_issue', response.data['errors'])
        self.assertIn('additional_details', response.data['errors'])

    def test_submit_ticket_whitespace_stripping(self):
        """Test that whitespace is stripped from input fields"""
        data = self.valid_data.copy()
        data['name'] = '  John  '
        data['surname'] = '  Doe  '
        data['k_number'] = '  12345678  '
        data['k_email'] = '  12345678@kcl.ac.uk  '
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify whitespace was stripped
        ticket = Ticket.objects.get(k_number='12345678')
        self.assertEqual(ticket.name, 'John')
        self.assertEqual(ticket.surname, 'Doe')
        self.assertEqual(ticket.k_email, '12345678@kcl.ac.uk')

    def test_submit_ticket_multiple_validation_errors(self):
        """Test submission with multiple validation errors"""
        data = {
            'name': 'John123',  # Contains numbers
            'surname': 'Doe456',  # Contains numbers
            'k_number': 'abc123',  # Contains letters
            'k_email': 'wrong@email.com',  # Wrong format
            'department': 'Invalid',  # Invalid department
            'type_of_issue': '',  # Missing
            'additional_details': ''  # Missing
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        # Should have multiple errors
        self.assertGreater(len(response.data['errors']), 1)

    def test_submit_ticket_special_characters_in_name(self):
        """Test submission with special characters in name (should be allowed)"""
        data = self.valid_data.copy()
        data['name'] = "O'Brien"
        data['k_number'] = '87654321'
        data['k_email'] = '87654321@kcl.ac.uk'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_ticket_long_k_number(self):
        """Test submission with a long K-Number"""
        data = self.valid_data.copy()
        data['k_number'] = '123456789012345'
        data['k_email'] = '123456789012345@kcl.ac.uk'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_ticket_get_method_not_allowed(self):
        """Test that GET method is not allowed"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
