from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from ..models import Ticket, Attachment
import os
import tempfile
import time


class AttachmentModelTest(TestCase):
    """Test cases for the Attachment model"""

    def setUp(self):
        """Set up test data"""
        self.ticket = Ticket.objects.create(
            name='John',
            surname='Doe',
            k_number='12345678',
            k_email='K12345678@kcl.ac.uk',
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help installing Python'
        )
        self.test_file = SimpleUploadedFile(
            "test_file.pdf",
            b"file content",
            content_type="application/pdf"
        )

    def test_attachment_creation(self):
        """Test creating an attachment"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file,
            original_filename='test_file.pdf'
        )
        self.assertEqual(attachment.ticket, self.ticket)
        self.assertEqual(attachment.original_filename, 'test_file.pdf')
        self.assertIsNotNone(attachment.uploaded_at)
        self.assertIsNotNone(attachment.file_size)

    def test_attachment_str_method(self):
        """Test the __str__ method of Attachment model"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file,
            original_filename='test_file.pdf'
        )
        expected_str = f"test_file.pdf - Ticket #{self.ticket.id}"
        self.assertEqual(str(attachment), expected_str)

    def test_attachment_foreign_key_relationship(self):
        """Test that attachment is linked to ticket via foreign key"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file,
            original_filename='test_file.pdf'
        )
        # Test forward relationship
        self.assertEqual(attachment.ticket, self.ticket)
        # Test reverse relationship
        self.assertIn(attachment, self.ticket.attachments.all())

    def test_attachment_cascade_delete(self):
        """Test that attachments are deleted when ticket is deleted"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file,
            original_filename='test_file.pdf'
        )
        attachment_id = attachment.id
        # Delete the ticket
        self.ticket.delete()
        # Attachment should also be deleted
        self.assertFalse(Attachment.objects.filter(id=attachment_id).exists())

    def test_attachment_original_filename_auto_set(self):
        """Test that original_filename is automatically set from file name"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file
        )
        self.assertEqual(attachment.original_filename, 'test_file.pdf')

    def test_attachment_file_size_auto_set(self):
        """Test that file_size is automatically set"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file,
            original_filename='test_file.pdf'
        )
        self.assertEqual(attachment.file_size, len(b"file content"))

    def test_attachment_upload_path(self):
        """Test that file is uploaded to correct path"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file,
            original_filename='test_file.pdf'
        )
        # Django adds random suffix to prevent collisions, so check for path pattern
        expected_path_pattern = f'attachments/ticket_{self.ticket.id}/'
        self.assertIn(expected_path_pattern, attachment.file.name)
        self.assertIn('test_file', attachment.file.name)
        self.assertTrue(attachment.file.name.endswith('.pdf'))

    def test_attachment_ordering(self):
        """Test that attachments are ordered by uploaded_at descending"""
        file1 = SimpleUploadedFile("file1.pdf", b"content1", content_type="application/pdf")
        file2 = SimpleUploadedFile("file2.pdf", b"content2", content_type="application/pdf")
        
        attachment1 = Attachment.objects.create(
            ticket=self.ticket,
            file=file1,
            original_filename='file1.pdf'
        )
        # Add a small delay to ensure different timestamps
        time.sleep(0.01)
        attachment2 = Attachment.objects.create(
            ticket=self.ticket,
            file=file2,
            original_filename='file2.pdf'
        )
        
        attachments = list(Attachment.objects.all())
        # Most recent should be first (attachment2 was created after attachment1)
        self.assertEqual(attachments[0], attachment2)
        self.assertEqual(attachments[1], attachment1)
        # Verify the ordering is correct by checking timestamps
        self.assertGreaterEqual(attachments[0].uploaded_at, attachments[1].uploaded_at)

    def test_multiple_attachments_per_ticket(self):
        """Test that a ticket can have multiple attachments"""
        file1 = SimpleUploadedFile("file1.pdf", b"content1", content_type="application/pdf")
        file2 = SimpleUploadedFile("file2.pdf", b"content2", content_type="application/pdf")
        
        attachment1 = Attachment.objects.create(
            ticket=self.ticket,
            file=file1,
            original_filename='file1.pdf'
        )
        attachment2 = Attachment.objects.create(
            ticket=self.ticket,
            file=file2,
            original_filename='file2.pdf'
        )
        
        self.assertEqual(self.ticket.attachments.count(), 2)
        self.assertIn(attachment1, self.ticket.attachments.all())
        self.assertIn(attachment2, self.ticket.attachments.all())

    def test_attachment_meta_options(self):
        """Test Attachment model Meta options"""
        self.assertEqual(Attachment._meta.verbose_name, 'Attachment')
        self.assertEqual(Attachment._meta.verbose_name_plural, 'Attachments')
        self.assertEqual(Attachment._meta.ordering, ['-uploaded_at'])

    def test_attachment_with_different_file_types(self):
        """Test creating attachments with different file types"""
        # Test PDF
        pdf_file = SimpleUploadedFile("test.pdf", b"pdf content", content_type="application/pdf")
        pdf_attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=pdf_file,
            original_filename='test.pdf'
        )
        self.assertEqual(pdf_attachment.original_filename, 'test.pdf')
        
        # Test image
        image_file = SimpleUploadedFile("test.jpg", b"image content", content_type="image/jpeg")
        image_attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=image_file,
            original_filename='test.jpg'
        )
        self.assertEqual(image_attachment.original_filename, 'test.jpg')
        
        # Test document
        doc_file = SimpleUploadedFile("test.docx", b"doc content", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        doc_attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=doc_file,
            original_filename='test.docx'
        )
        self.assertEqual(doc_attachment.original_filename, 'test.docx')

    def test_attachment_original_filename_preserved(self):
        """Test that original filename is preserved even if file name changes"""
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=self.test_file,
            original_filename='original_name.pdf'
        )
        # Even if file.name changes, original_filename should remain
        self.assertEqual(attachment.original_filename, 'original_name.pdf')

