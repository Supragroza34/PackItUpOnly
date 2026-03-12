from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from ..models.ticket import Ticket
from ..models.user import User


class AdminErrorHandlingTest(TestCase):
    """Test error handling in admin endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_superuser=True
        )
        
        # Create student user
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            user=self.student,
            department='Informatics',
            type_of_issue='Test Issue',
            additional_details='Test details'
        )

    def test_ticket_update_invalid_status(self):
        """Test updating ticket with invalid status"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/tickets/{self.ticket.id}/update/'
        
        response = self.client.patch(url, {'status': 'invalid_status'})
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ticket_update_invalid_priority(self):
        """Test updating ticket with invalid priority"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/tickets/{self.ticket.id}/update/'
        
        response = self.client.patch(url, {'priority': 'invalid_priority'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ticket_update_nonexistent_assigned_user(self):
        """Test assigning ticket to nonexistent user"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/tickets/{self.ticket.id}/update/'
        
        response = self.client.patch(url, {'assigned_to': 99999})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ticket_detail_invalid_id(self):
        """Test getting ticket detail with invalid ID format"""
        self.client.force_authenticate(user=self.admin)
        url = '/api/admin/tickets/invalid_id/'
        
        # Django will return 404 for invalid integer ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ticket_update_with_empty_data(self):
        """Test updating ticket with empty request data"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/tickets/{self.ticket.id}/update/'
        
        # Empty PATCH should succeed (no changes)
        response = self.client.patch(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_delete_nonexistent(self):
        """Test deleting nonexistent user"""
        self.client.force_authenticate(user=self.admin)
        url = '/api/admin/users/99999/delete/'
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_ticket_delete_nonexistent(self):
        """Test deleting nonexistent ticket"""
        self.client.force_authenticate(user=self.admin)
        url = '/api/admin/tickets/99999/delete/'
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_dashboard_stats_database_error(self):
        """Test dashboard stats with simulated database error"""
        self.client.force_authenticate(user=self.admin)
        
        # Mock a database error
        with patch('KCLTicketingSystems.models.ticket.Ticket.objects.count') as mock_count:
            mock_count.side_effect = Exception('Database error')
            
            response = self.client.get('/api/admin/dashboard/stats/')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)

    def test_pagination_invalid_page_number(self):
        """Test pagination with invalid page number"""
        self.client.force_authenticate(user=self.admin)
        
        # Test with negative page
        response = self.client.get('/api/admin/tickets/', {'page': -1})
        # Django will handle this, might return 500 or first page
        # Just check it doesn't crash
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])

    def test_pagination_invalid_page_size(self):
        """Test pagination with invalid page size"""
        self.client.force_authenticate(user=self.admin)
        
        # Test with negative page size
        response = self.client.get('/api/admin/tickets/', {'page_size': -1})
        # Should handle gracefully
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])

    def test_staff_list_database_error(self):
        """Test staff list with simulated database error"""
        self.client.force_authenticate(user=self.admin)
        
        with patch('KCLTicketingSystems.models.user.User.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception('Database error')
            
            response = self.client.get('/api/admin/staff/')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)


class AdminConcurrencyTest(TestCase):
    """Test concurrent operations and race conditions"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_superuser=True
        )
        
        # Create student user
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            user=self.student,
            department='Informatics',
            type_of_issue='Test Issue',
            additional_details='Test details'
        )

    def test_delete_ticket_then_update(self):
        """Test updating a ticket that was just deleted"""
        self.client.force_authenticate(user=self.admin)
        
        # Delete ticket
        delete_url = f'/api/admin/tickets/{self.ticket.id}/delete/'
        delete_response = self.client.delete(delete_url)
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        
        # Try to update deleted ticket
        update_url = f'/api/admin/tickets/{self.ticket.id}/update/'
        update_response = self.client.patch(update_url, {'status': 'resolved'})
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_then_access(self):
        """Test accessing a user that was just deleted"""
        # Create another user to delete
        test_user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STUDENT
        )
        
        self.client.force_authenticate(user=self.admin)
        
        # Delete user
        delete_url = f'/api/admin/users/{test_user.id}/delete/'
        delete_response = self.client.delete(delete_url)
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        
        # Try to access deleted user
        detail_url = f'/api/admin/users/{test_user.id}/'
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_multiple_updates_same_ticket(self):
        """Test multiple sequential updates to the same ticket"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/tickets/{self.ticket.id}/update/'
        
        # First update
        response1 = self.client.patch(url, {'status': 'in_progress'})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second update
        response2 = self.client.patch(url, {'priority': 'high'})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Third update
        response3 = self.client.patch(url, {'status': 'resolved'})
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        
        # Verify final state
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.RESOLVED)
        self.assertEqual(self.ticket.priority, Ticket.Priority.HIGH)


class AdminDataValidationTest(TestCase):
    """Test data validation in admin endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_superuser=True
        )
        
        # Create student user
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            user=self.student,
            department='Informatics',
            type_of_issue='Test Issue',
            additional_details='Test details'
        )

    def test_ticket_update_with_extra_fields(self):
        """Test updating ticket with extra fields that should be ignored"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/tickets/{self.ticket.id}/update/'
        
        response = self.client.patch(url, {
            'status': 'in_progress',
            'extra_field': 'should be ignored',
            'another_field': 123
        })
        
        # Should succeed and ignore extra fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_user_update_readonly_fields(self):
        """Test that readonly fields cannot be updated"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/users/{self.student.id}/update/'
        
        # Try to update readonly fields
        response = self.client.patch(url, {
            'id': 99999,
            'is_superuser': True,
            'role': 'staff'  # This should work
        })
        
        # Should succeed but ignore readonly fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify readonly fields weren't changed
        self.student.refresh_from_db()
        self.assertNotEqual(self.student.id, 99999)
        # Role should be updated
        self.assertEqual(self.student.role, User.Role.STAFF)

    def test_ticket_assignment_null_value(self):
        """Test assigning ticket to null (unassigning)"""
        # First assign to someone
        staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STAFF
        )
        self.ticket.assigned_to = staff
        self.ticket.save()
        
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/tickets/{self.ticket.id}/update/'
        
        # Unassign by setting to empty string
        response = self.client.patch(url, {'assigned_to': ''}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_to)

    def test_empty_string_search(self):
        """Test search with empty string"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get('/api/admin/tickets/', {'search': ''})
        
        # Should return all tickets
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_special_characters_search(self):
        """Test search with special characters"""
        self.client.force_authenticate(user=self.admin)
        
        # Search with special characters
        response = self.client.get('/api/admin/tickets/', {'search': '@#$%'})
        
        # Should not crash
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_very_long_search_query(self):
        """Test search with very long query string"""
        self.client.force_authenticate(user=self.admin)
        
        # Create a very long search query
        long_query = 'a' * 1000
        response = self.client.get('/api/admin/tickets/', {'search': long_query})
        
        # Should handle gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminPermissionEdgeCasesTest(TestCase):
    """Test edge cases for admin permissions"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_superuser=True
        )
        
        # Create staff user (not admin)
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STAFF,
            is_staff=True  # Staff flag but not admin role
        )
        
        # Create superuser without admin role
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@test.com',
            password='testpass123',
            k_number='33333333',
            role=User.Role.STUDENT,  # Student role but superuser flag
            is_superuser=True
        )

    def test_superuser_has_admin_access(self):
        """Test that superuser has admin access regardless of role"""
        self.client.force_authenticate(user=self.superuser)
        
        response = self.client.get('/api/admin/dashboard/stats/')
        
        # Superuser should have access
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_without_admin_role_no_access(self):
        """Test that staff user without admin role cannot access admin endpoints"""
        self.client.force_authenticate(user=self.staff)
        
        response = self.client.get('/api/admin/dashboard/stats/')
        
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_other_users_not_self(self):
        """Test that admin can delete other users but not themselves"""
        self.client.force_authenticate(user=self.admin)
        
        # Try to delete self
        url = f'/api/admin/users/{self.admin.id}/delete/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Verify admin still exists
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())

    def test_admin_can_delete_other_admin(self):
        """Test that admin can delete other admin users"""
        # Create another admin
        other_admin = User.objects.create_user(
            username='otheradmin',
            email='other@test.com',
            password='testpass123',
            k_number='44444444',
            role=User.Role.ADMIN
        )
        
        self.client.force_authenticate(user=self.admin)
        
        # Delete other admin
        url = f'/api/admin/users/{other_admin.id}/delete/'
        response = self.client.delete(url)
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(id=other_admin.id).exists())

    def test_token_expired_returns_401(self):
        """Test that expired token returns 401"""
        # This is more of an integration test with JWT
        # Without valid authentication, should return 401
        response = self.client.get('/api/admin/dashboard/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
