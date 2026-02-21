from django.test import TestCase, Client
from django.urls import reverse
from django.utils.html import escape
from ..models import Ticket


class TicketFormViewTest(TestCase):
    """Test cases for the Ticket Form HTML view"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('ticket_form')

    def test_ticket_form_page_loads(self):
        """Test that the ticket form page loads successfully"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ticket_form.html')

    def test_ticket_form_contains_all_fields(self):
        """Test that the form contains all required fields"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for all form fields
        self.assertIn('name', content)
        self.assertIn('surname', content)
        self.assertIn('k_number', content)
        self.assertIn('k_email', content)
        self.assertIn('department', content)
        self.assertIn('type_of_issue', content)
        self.assertIn('additional_details', content)
        self.assertIn('Submit Ticket', content)

    def test_ticket_form_contains_departments(self):
        """Test that the form contains all three departments"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('Informatics', content)
        self.assertIn('Engineering', content)
        self.assertIn('Medicine', content)

    def test_ticket_form_contains_bootstrap(self):
        """Test that Bootstrap 5.3 is included"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('bootstrap@5.3.0', content)
        self.assertIn('bootstrap.min.css', content)
        # Template uses bootstrap.bundle.min.js (not bootstrap.min.js)
        self.assertIn('bootstrap.bundle.min.js', content)

    def test_ticket_form_contains_csrf_token(self):
        """Test that CSRF token is present in the form"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('csrfmiddlewaretoken', content)

    def test_ticket_form_k_number_maxlength(self):
        """Test that K number input has maxlength attribute"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('maxlength="8"', content)

    def test_ticket_form_email_readonly(self):
        """Test that email field is readonly"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('readonly', content)

    def test_ticket_form_contains_issue_types_script(self):
        """Test that JavaScript contains issue types for all departments"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for Informatics issues
        self.assertIn('Software Installation Issues', content)
        self.assertIn('Network Connectivity Problems', content)
        
        # Check for Engineering issues
        self.assertIn('Lab Equipment Malfunction', content)
        self.assertIn('CAD Software Issues', content)
        
        # Check for Medicine issues
        self.assertIn('Clinical System Access', content)
        self.assertIn('Medical Database Query', content)


class TicketFormKNumberValidationTest(TestCase):
    """Test cases for K Number validation in the form"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('ticket_form')

    def test_k_number_field_present(self):
        """Test that K number field is present in the form"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('id="k_number"', content)
        self.assertIn('name="k_number"', content)

    def test_k_number_placeholder(self):
        """Test that K number field has appropriate placeholder"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('Enter your K-Number', content)

    def test_email_auto_generation_script(self):
        """Test that JavaScript includes email auto-generation logic"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for email auto-generation logic
        self.assertIn('kEmailInput.value', content)
        self.assertIn('@kcl.ac.uk', content)


class TicketFormEmailValidationTest(TestCase):
    """Test cases for Email validation in the form"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('ticket_form')

    def test_email_field_present(self):
        """Test that email field is present in the form"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('id="k_email"', content)
        self.assertIn('name="k_email"', content)

    def test_email_field_readonly(self):
        """Test that email field is readonly"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('readonly', content)

    def test_email_placeholder(self):
        """Test that email field has appropriate placeholder"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('KNumber@kcl.ac.uk', content)


class TicketFormDepartmentTest(TestCase):
    """Test cases for Department selection in the form"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('ticket_form')

    def test_department_select_present(self):
        """Test that department select is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('id="department"', content)
        self.assertIn('name="department"', content)

    def test_all_departments_present(self):
        """Test that all three departments are in the select"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('<option value="Informatics">Informatics</option>', content)
        self.assertIn('<option value="Engineering">Engineering</option>', content)
        self.assertIn('<option value="Medicine">Medicine</option>', content)

    def test_type_of_issue_container_hidden_initially(self):
        """Test that type of issue container is hidden initially"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('display: none', content)

    def test_type_of_issue_select_present(self):
        """Test that type of issue select is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('id="type_of_issue"', content)
        self.assertIn('name="type_of_issue"', content)


class TicketFormIntegrationTest(TestCase):
    """Integration tests for the ticket form"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.form_url = reverse('ticket_form')
        self.submit_url = reverse('submit_ticket')

    def test_form_submission_flow(self):
        """Test the complete form submission flow"""
        # First, get the form page
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, 200)
        
        # Then submit valid data
        valid_data = {
            'name': 'John',
            'surname': 'Doe',
            'k_number': '12345678',
            'k_email': 'K12345678@kcl.ac.uk',
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python'
        }
        
        response = self.client.post(
            self.submit_url,
            data=valid_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], 'Ticket submitted successfully')

    def test_form_validation_errors_displayed(self):
        """Test that validation errors are properly handled"""
        # Submit invalid data
        invalid_data = {
            'name': '',
            'surname': '',
            'k_number': '',
            'k_email': '',
            'department': '',
            'type_of_issue': '',
            'additional_details': ''
        }
        
        response = self.client.post(
            self.submit_url,
            data=invalid_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())


class TicketFormJavaScriptTest(TestCase):
    """Test cases for JavaScript functionality in the form"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('ticket_form')

    def test_javascript_k_number_filtering(self):
        """Test that JavaScript includes K number filtering logic"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for number filtering logic
        self.assertIn('replace(/[^0-9]/g', content)
        self.assertIn('.slice(0, 8)', content)

    def test_javascript_email_generation(self):
        """Test that JavaScript includes email generation logic"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for email generation
        self.assertIn('K${value}@kcl.ac.uk', content)

    def test_javascript_department_change_handler(self):
        """Test that JavaScript includes department change handler"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for department change event listener
        self.assertIn('departmentSelect.addEventListener', content)

    def test_javascript_form_submission_handler(self):
        """Test that JavaScript includes form submission handler"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for form submit event listener
        self.assertIn('form.addEventListener', content)
        self.assertIn('submit', content)

    def test_javascript_error_handling(self):
        """Test that JavaScript includes error handling"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for error handling functions
        self.assertIn('showFieldError', content)
        self.assertIn('clearFieldError', content)
        self.assertIn('showErrorMessage', content)

    def test_javascript_success_message(self):
        """Test that JavaScript includes success message handling"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for success message handling
        self.assertIn('showSuccessMessage', content)
        self.assertIn('success-message', content)

    def test_javascript_client_side_validation(self):
        """Test that JavaScript includes client-side validation"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for validation logic
        self.assertIn('validate', content.lower())
        self.assertIn('required', content.lower())


class TicketFormBootstrapTest(TestCase):
    """Test cases for Bootstrap 5.3 integration"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('ticket_form')

    def test_bootstrap_css_included(self):
        """Test that Bootstrap CSS is included"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('bootstrap@5.3.0/dist/css/bootstrap.min.css', content)

    def test_bootstrap_js_included(self):
        """Test that Bootstrap JS is included"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js', content)

    def test_bootstrap_classes_used(self):
        """Test that Bootstrap classes are used in the form"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for common Bootstrap classes
        self.assertIn('container', content)
        self.assertIn('form-control', content)
        self.assertIn('form-select', content)
        self.assertIn('btn btn-primary', content)
        self.assertIn('mb-3', content)
        self.assertIn('form-label', content)

    def test_bootstrap_validation_classes(self):
        """Test that Bootstrap validation classes are used"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for Bootstrap validation classes
        self.assertIn('is-invalid', content)
        self.assertIn('invalid-feedback', content)

