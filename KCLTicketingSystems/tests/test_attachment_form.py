from django.test import TestCase, Client
from django.urls import reverse


class AttachmentFormTest(TestCase):
    """Test cases for file attachment functionality in the ticket form"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('ticket_form')

    def test_file_input_field_present(self):
        """Test that file input field is present in the form"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('id="attachments"', content)
        self.assertIn('name="attachments"', content)
        self.assertIn('type="file"', content)
        self.assertIn('multiple', content)

    def test_file_input_accept_attribute(self):
        """Test that file input has accept attribute for file types"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for accept attribute with allowed file types
        self.assertIn('accept=', content)
        self.assertIn('image/*', content)
        self.assertIn('.pdf', content)
        self.assertIn('.doc', content)
        self.assertIn('.docx', content)
        self.assertIn('.txt', content)

    def test_file_input_label_present(self):
        """Test that file input has a label"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('Attachments (Optional)', content)

    def test_file_input_help_text_present(self):
        """Test that file input has help text"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('You can upload images', content)
        self.assertIn('Maximum file size: 10MB per file', content)

    def test_file_list_container_present(self):
        """Test that file list display container is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        self.assertIn('id="file-list"', content)

    def test_file_handling_javascript_present(self):
        """Test that JavaScript for file handling is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file handling JavaScript
        self.assertIn('attachmentsInput.addEventListener', content)
        self.assertIn('selectedFiles', content)
        self.assertIn('updateFileList', content)
        self.assertIn('formatFileSize', content)

    def test_file_validation_javascript_present(self):
        """Test that JavaScript for file validation is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file validation
        self.assertIn('MAX_FILE_SIZE', content)
        self.assertIn('10 * 1024 * 1024', content)
        self.assertIn('oversizedFiles', content)

    def test_file_removal_javascript_present(self):
        """Test that JavaScript for file removal is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file removal functionality
        self.assertIn('remove-file', content)
        self.assertIn('splice', content)

    def test_formdata_submission_javascript(self):
        """Test that JavaScript uses FormData for file submission"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for FormData usage
        self.assertIn('FormData', content)
        self.assertIn('formDataToSend', content)
        self.assertIn('append', content)

    def test_file_css_styles_present(self):
        """Test that CSS styles for file items are present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file item styles
        self.assertIn('.file-item', content)
        self.assertIn('.file-name', content)
        self.assertIn('.file-size', content)
        self.assertIn('.remove-file', content)

    def test_file_input_position_in_form(self):
        """Test that file input is positioned correctly in the form"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # File input should be after additional_details and before submit button
        additional_details_index = content.find('additional_details')
        attachments_index = content.find('id="attachments"')
        submit_button_index = content.find('Submit Ticket')
        
        self.assertGreater(attachments_index, additional_details_index)
        self.assertLess(attachments_index, submit_button_index)

    def test_file_input_optional_indicator(self):
        """Test that file input is marked as optional"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for optional indicator
        self.assertIn('(Optional)', content)

    def test_file_size_formatting_function(self):
        """Test that file size formatting function is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file size formatting
        self.assertIn('formatFileSize', content)
        self.assertIn('Bytes', content)
        self.assertIn('KB', content)
        self.assertIn('MB', content)

    def test_file_list_update_function(self):
        """Test that file list update function is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file list update
        self.assertIn('updateFileList', content)
        self.assertIn('fileItem', content)

    def test_file_input_update_function(self):
        """Test that file input update function is present"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file input update
        self.assertIn('updateFileInput', content)
        self.assertIn('DataTransfer', content)

    def test_file_validation_before_submission(self):
        """Test that file validation occurs before form submission"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file validation before submission
        self.assertIn('Validate file sizes', content)
        self.assertIn('selectedFiles.length', content)

    def test_file_reset_on_success(self):
        """Test that files are reset after successful submission"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        
        # Check for file reset on success
        self.assertIn('selectedFiles = []', content)
        self.assertIn('updateFileList()', content)

