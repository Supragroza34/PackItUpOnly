from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response

from ..permissions import IsAdmin
from ..models.user import User


class TestView(APIView):
    """Test view using IsAdmin permission"""
    permission_classes = [IsAdmin]
    
    def get(self, request):
        return Response({'message': 'Access granted'})


class IsAdminPermissionTest(TestCase):
    """Test cases for IsAdmin permission class"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.permission = IsAdmin()
        self.view = TestView.as_view()
        
        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='88888888',
            role=User.Role.STAFF,
            is_staff=True
        )
        
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@test.com',
            password='testpass123',
            k_number='77777777',
            role=User.Role.STUDENT,  # Even with student role
            is_superuser=True
        )
        
        self.student_user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )

    def test_admin_role_has_permission(self):
        """Test that user with admin role has permission"""
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        permission = self.permission.has_permission(request, TestView)
        self.assertTrue(permission)

    def test_staff_user_no_permission(self):
        """Test that staff users do not have admin permission"""
        request = self.factory.get('/test/')
        request.user = self.staff_user
        
        permission = self.permission.has_permission(request, TestView)
        self.assertFalse(permission)

    def test_superuser_has_permission(self):
        """Test that superuser has permission"""
        request = self.factory.get('/test/')
        request.user = self.superuser
        
        permission = self.permission.has_permission(request, TestView)
        self.assertTrue(permission)

    def test_student_no_permission(self):
        """Test that regular student user does not have permission"""
        request = self.factory.get('/test/')
        request.user = self.student_user
        
        permission = self.permission.has_permission(request, TestView)
        self.assertFalse(permission)

    def test_unauthenticated_user_no_permission(self):
        """Test that unauthenticated user does not have permission"""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        permission = self.permission.has_permission(request, TestView)
        self.assertFalse(permission)

    def test_none_user_no_permission(self):
        """Test that None user does not have permission"""
        request = self.factory.get('/test/')
        request.user = None
        
        permission = self.permission.has_permission(request, TestView)
        self.assertFalse(permission)

    def test_staff_role_with_is_staff_flag(self):
        """Test that staff role users do not have admin permission even with is_staff flag"""
        staff_with_flag = User.objects.create_user(
            username='staff2',
            email='staff2@test.com',
            password='testpass123',
            k_number='66666666',
            role=User.Role.STAFF,
            is_staff=True
        )
        
        request = self.factory.get('/test/')
        request.user = staff_with_flag
        
        permission = self.permission.has_permission(request, TestView)
        self.assertFalse(permission)

    def test_multiple_admin_attributes(self):
        """Test user with multiple admin attributes"""
        multi_admin = User.objects.create_user(
            username='multiadmin',
            email='multiadmin@test.com',
            password='testpass123',
            k_number='55555555',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        
        request = self.factory.get('/test/')
        request.user = multi_admin
        
        permission = self.permission.has_permission(request, TestView)
        self.assertTrue(permission)

    def test_permission_class_name(self):
        """Test permission class name and docstring"""
        self.assertEqual(self.permission.__class__.__name__, 'IsAdmin')
        self.assertIsNotNone(self.permission.__class__.__doc__)

    def test_has_permission_method_exists(self):
        """Test that has_permission method exists"""
        self.assertTrue(hasattr(self.permission, 'has_permission'))
        self.assertTrue(callable(self.permission.has_permission))
