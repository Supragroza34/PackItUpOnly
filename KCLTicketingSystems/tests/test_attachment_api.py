from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import MagicMock
from ..models import Ticket, Attachment
from ..models.attachment import attachment_upload_path
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
        
        ticket = Ticket.objects.get(k_number='12345678')
        self.assertEqual(ticket.attachments.count(), 0)

    def test_submit_ticket_with_oversized_file(self):
        """Test submitting a ticket with a file larger than 10MB"""
        large_content = b"x" * (11 * 1024 * 1024)
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
        exact_size_content = b"x" * (10 * 1024 * 1024)
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


class AttachmentModelUnitTests(TestCase):
    """Unit tests targeting model-level branches for 100% coverage."""

    def setUp(self):
        self.ticket = Ticket.objects.create(
            name='John',
            surname='Doe',
            k_number='12340000',
            k_email='K12340000@kcl.ac.uk',
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Test'
        )

    def test_upload_path_with_ticket_id(self):
        """Covers the if branch in attachment_upload_path."""
        mock_instance = MagicMock()
        mock_instance.ticket.id = 42
        result = attachment_upload_path(mock_instance, 'test.pdf')
        self.assertEqual(result, 'attachments/ticket_42/test.pdf')

    def test_upload_path_fallback_no_ticket(self):
        """Covers the else branch when ticket is None."""
        mock_instance = MagicMock()
        mock_instance.ticket = None
        result = attachment_upload_path(mock_instance, 'test.pdf')
        self.assertEqual(result, 'attachments/temp/test.pdf')

    def test_upload_path_fallback_no_ticket_id(self):
        """Covers the else branch when ticket has no ID."""
        mock_instance = MagicMock()
        mock_instance.ticket.id = None
        result = attachment_upload_path(mock_instance, 'test.pdf')
        self.assertEqual(result, 'attachments/temp/test.pdf')

    def test_save_does_not_overwrite_existing_original_filename(self):
        """Covers the `not self.original_filename` branch being False."""
        pdf_file = SimpleUploadedFile("new.pdf", b"content", content_type="application/pdf")
        attachment = Attachment(
            ticket=self.ticket,
            file=pdf_file,
            original_filename='already_set.pdf',
            file_size=0,
        )
        attachment.save()
        self.assertEqual(attachment.original_filename, 'already_set.pdf')

    def test_save_without_file(self):
        """Covers the `if self.file` branch being False."""
        attachment = Attachment(
            ticket=self.ticket,
            original_filename='manual.pdf',
            file_size=999,
        )
        attachment.save()
        self.assertEqual(attachment.file_size, 999)

    def test_str_representation(self):
        """Covers the __str__ method."""
        attachment = Attachment(
            ticket=self.ticket,
            original_filename='report.pdf',
            file_size=1024,
        )
        self.assertEqual(str(attachment), f"report.pdf - Ticket #{self.ticket.id}")