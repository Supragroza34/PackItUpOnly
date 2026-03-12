from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Ticket, Attachment
import io


class AttachmentAPITest(TestCase):
    """Test cases for file attachment functionality in the API"""

    def setUp(self):
        """Set up test client and valid data"""
        self.client = APIClient()
        self.url = '/api/submit-ticket/'
        self.valid_data = {
            'name': 'John',
            'surname': 'Doe',
            'k_number': '12345678',
            'k_email': 'K12345678@kcl.ac.uk',
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python'
        }

    def test_submit_ticket_with_single_attachment(self):
        """Test submitting a ticket with a single file attachment"""
        pdf_file = SimpleUploadedFile(
            "test_file.pdf",
            b"file content",
            content_type="application/pdf"
        )
        
        data = self.valid_data.copy()
        response = self.client.post(
            self.url,
            {**data, 'attachments': [pdf_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('attachments_count', response.data)
        self.assertEqual(response.data['attachments_count'], 1)
        
        # Verify ticket was created
        ticket = Ticket.objects.get(k_number='12345678')
        self.assertEqual(ticket.attachments.count(), 1)
        attachment = ticket.attachments.first()
        self.assertEqual(attachment.original_filename, 'test_file.pdf')

    def test_submit_ticket_with_multiple_attachments(self):
        """Test submitting a ticket with multiple file attachments"""
        file1 = SimpleUploadedFile("file1.pdf", b"content1", content_type="application/pdf")
        file2 = SimpleUploadedFile("file2.jpg", b"content2", content_type="image/jpeg")
        file3 = SimpleUploadedFile("file3.txt", b"content3", content_type="text/plain")
        
        data = self.valid_data.copy()
        data['k_number'] = '87654321'
        data['k_email'] = 'K87654321@kcl.ac.uk'
        
        response = self.client.post(
            self.url,
            {**data, 'attachments': [file1, file2, file3]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments_count'], 3)
        
        # Verify all attachments were created
        ticket = Ticket.objects.get(k_number='87654321')
        self.assertEqual(ticket.attachments.count(), 3)

    def test_submit_ticket_without_attachments(self):
        """Test submitting a ticket without any attachments (should still work)"""
        response = self.client.post(
            self.url,
            self.valid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('attachments_count', response.data)
        self.assertEqual(response.data['attachments_count'], 0)
        
        # Verify ticket was created
        ticket = Ticket.objects.get(k_number='12345678')
        self.assertEqual(ticket.attachments.count(), 0)

    def test_submit_ticket_with_oversized_file(self):
        """Test submitting a ticket with a file larger than 10MB"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large_file.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        data = self.valid_data.copy()
        response = self.client.post(
            self.url,
            {**data, 'attachments': [large_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('attachments', response.data['errors'])
        self.assertIn('exceeds the maximum file size', response.data['errors']['attachments'])

    def test_submit_ticket_with_invalid_file_type(self):
        """Test submitting a ticket with an invalid file type"""
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"executable content",
            content_type="application/x-msdownload"
        )
        
        data = self.valid_data.copy()
        data['k_number'] = '11111111'
        data['k_email'] = 'K11111111@kcl.ac.uk'
        
        response = self.client.post(
            self.url,
            {**data, 'attachments': [invalid_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('attachments', response.data['errors'])
        self.assertIn('invalid file type', response.data['errors']['attachments'])

    def test_submit_ticket_with_valid_image_types(self):
        """Test submitting tickets with valid image file types"""
        valid_image_types = [
            ('test.jpg', 'image/jpeg'),
            ('test.jpeg', 'image/jpeg'),
            ('test.png', 'image/png'),
            ('test.gif', 'image/gif'),
        ]
        
        for filename, content_type in valid_image_types:
            image_file = SimpleUploadedFile(
                filename,
                b"image content",
                content_type=content_type
            )
            
            data = self.valid_data.copy()
            data['k_number'] = f'1234567{valid_image_types.index((filename, content_type))}'
            data['k_email'] = f'K{data["k_number"]}@kcl.ac.uk'
            
            response = self.client.post(
                self.url,
                {**data, 'attachments': [image_file]},
                format='multipart'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, 
                           f"Failed for {filename}")

    def test_submit_ticket_with_valid_document_types(self):
        """Test submitting tickets with valid document file types"""
        valid_doc_types = [
            ('test.pdf', 'application/pdf'),
            ('test.doc', 'application/msword'),
            ('test.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('test.txt', 'text/plain'),
        ]
        
        for filename, content_type in valid_doc_types:
            doc_file = SimpleUploadedFile(
                filename,
                b"document content",
                content_type=content_type
            )
            
            data = self.valid_data.copy()
            data['k_number'] = f'8765432{valid_doc_types.index((filename, content_type))}'
            data['k_email'] = f'K{data["k_number"]}@kcl.ac.uk'
            
            response = self.client.post(
                self.url,
                {**data, 'attachments': [doc_file]},
                format='multipart'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                           f"Failed for {filename}")

    def test_submit_ticket_file_size_exactly_10mb(self):
        """Test submitting a file exactly at the 10MB limit (should pass)"""
        # Create a file exactly 10MB
        exact_size_content = b"x" * (10 * 1024 * 1024)  # Exactly 10MB
        exact_file = SimpleUploadedFile(
            "exact_10mb.pdf",
            exact_size_content,
            content_type="application/pdf"
        )
        
        data = self.valid_data.copy()
        data['k_number'] = '99999999'
        data['k_email'] = 'K99999999@kcl.ac.uk'
        
        response = self.client.post(
            self.url,
            {**data, 'attachments': [exact_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_ticket_multiple_files_one_invalid(self):
        """Test submitting multiple files where one is invalid"""
        valid_file = SimpleUploadedFile("valid.pdf", b"content", content_type="application/pdf")
        invalid_file = SimpleUploadedFile("invalid.exe", b"content", content_type="application/x-msdownload")
        
        data = self.valid_data.copy()
        data['k_number'] = '55555555'
        data['k_email'] = 'K55555555@kcl.ac.uk'
        
        response = self.client.post(
            self.url,
            {**data, 'attachments': [valid_file, invalid_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('attachments', response.data['errors'])

    def test_submit_ticket_multiple_files_one_oversized(self):
        """Test submitting multiple files where one is oversized"""
        valid_file = SimpleUploadedFile("valid.pdf", b"content", content_type="application/pdf")
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (11 * 1024 * 1024),
            content_type="application/pdf"
        )
        
        data = self.valid_data.copy()
        data['k_number'] = '44444444'
        data['k_email'] = 'K44444444@kcl.ac.uk'
        
        response = self.client.post(
            self.url,
            {**data, 'attachments': [valid_file, large_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('attachments', response.data['errors'])

    def test_submit_ticket_json_format_still_works(self):
        """Test that JSON format submission still works (backward compatibility)"""
        response = self.client.post(
            self.url,
            self.valid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('ticket_id', response.data)
        # Should not have attachments_count if no files
        self.assertIn('attachments_count', response.data)
        self.assertEqual(response.data['attachments_count'], 0)

    def test_attachment_file_stored_correctly(self):
        """Test that attachment files are stored in the correct location"""
        pdf_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        
        data = self.valid_data.copy()
        response = self.client.post(
            self.url,
            {**data, 'attachments': [pdf_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        ticket = Ticket.objects.get(k_number='12345678')
        attachment = ticket.attachments.first()
        
        # Check that file path contains ticket ID (Django adds random suffix to prevent collisions)
        self.assertIn(f'ticket_{ticket.id}', attachment.file.name)
        self.assertIn('test', attachment.file.name)
        self.assertTrue(attachment.file.name.endswith('.pdf'))

    def test_attachment_metadata_saved(self):
        """Test that attachment metadata (filename, size) is saved correctly"""
        pdf_file = SimpleUploadedFile("original_name.pdf", b"file content here", content_type="application/pdf")
        
        data = self.valid_data.copy()
        data['k_number'] = '77777777'
        data['k_email'] = 'K77777777@kcl.ac.uk'
        
        response = self.client.post(
            self.url,
            {**data, 'attachments': [pdf_file]},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        ticket = Ticket.objects.get(k_number='77777777')
        attachment = ticket.attachments.first()
        
        self.assertEqual(attachment.original_filename, 'original_name.pdf')
        self.assertEqual(attachment.file_size, len(b"file content here"))
        self.assertIsNotNone(attachment.uploaded_at)

    def test_submit_ticket_with_empty_file_list(self):
        """Test submitting with empty attachments list"""
        data = self.valid_data.copy()
        data['k_number'] = '88888888'
        data['k_email'] = 'K88888888@kcl.ac.uk'
        
        response = self.client.post(
            self.url,
            {**data, 'attachments': []},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments_count'], 0)

