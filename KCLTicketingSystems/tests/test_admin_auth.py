from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from ..models.user import User


class JWTAuthenticationTest(TestCase):
    """Test cases for JWT authentication"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.token_url = '/api/auth/token/'
        self.refresh_url = '/api/auth/token/refresh/'
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            k_number='12345678',
            first_name='Test',
            last_name='User',
            role=User.Role.STUDENT
        )

    def test_token_obtain_success(self):
        """Test successful JWT token generation"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIsNotNone(response.data['access'])
        self.assertIsNotNone(response.data['refresh'])

    def test_token_obtain_invalid_credentials(self):
        """Test token generation with invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_obtain_missing_username(self):
        """Test token generation with missing username"""
        data = {
            'password': 'testpass123'
        }
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtain_missing_password(self):
        """Test token generation with missing password"""
        data = {
            'username': 'testuser'
        }
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtain_nonexistent_user(self):
        """Test token generation for non-existent user"""
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        response = self.client.post(self.token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_success(self):
        """Test successful token refresh"""
        # First get a token
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.token_url, login_data)
        refresh_token = login_response.data['refresh']
        
        # Now refresh it
        refresh_data = {
            'refresh': refresh_token
        }
        response = self.client.post(self.refresh_url, refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIsNotNone(response.data['access'])

    def test_token_refresh_invalid_token(self):
        """Test token refresh with invalid token"""
        refresh_data = {
            'refresh': 'invalid_token'
        }
        response = self.client.post(self.refresh_url, refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_missing_token(self):
        """Test token refresh with missing token"""
        response = self.client.post(self.refresh_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserRegistrationTest(TestCase):
    """Test cases for user registration"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        
        self.valid_registration_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'k_number': '12345678',
            'first_name': 'New',
            'last_name': 'User',
            'department': 'Informatics'
        }

    def test_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.k_number, '12345678')
        self.assertEqual(user.role, User.Role.STUDENT)  # Default role

    def test_registration_password_hashed(self):
        """Test that password is properly hashed"""
        response = self.client.post(self.register_url, self.valid_registration_data)
        
        user = User.objects.get(username='newuser')
        self.assertNotEqual(user.password, 'newpass123')  # Should be hashed
        self.assertTrue(user.check_password('newpass123'))  # But should verify correctly

    def test_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        # Create first user
        self.client.post(self.register_url, self.valid_registration_data)
        
        # Try to create another with same username
        duplicate_data = self.valid_registration_data.copy()
        duplicate_data['email'] = 'different@test.com'
        duplicate_data['k_number'] = '87654321'
        
        response = self.client.post(self.register_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create first user
        self.client.post(self.register_url, self.valid_registration_data)
        
        # Try to create another with same email
        duplicate_data = self.valid_registration_data.copy()
        duplicate_data['username'] = 'different'
        duplicate_data['k_number'] = '87654321'
        
        response = self.client.post(self.register_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_k_number(self):
        """Test registration with duplicate k_number"""
        # Create first user
        self.client.post(self.register_url, self.valid_registration_data)
        
        # Try to create another with same k_number
        duplicate_data = self.valid_registration_data.copy()
        duplicate_data['username'] = 'different'
        duplicate_data['email'] = 'different@test.com'
        
        response = self.client.post(self.register_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_missing_required_fields(self):
        """Test registration with missing required fields"""
        # Missing username
        data = self.valid_registration_data.copy()
        del data['username']
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing email
        data = self.valid_registration_data.copy()
        del data['email']
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing password
        data = self.valid_registration_data.copy()
        del data['password']
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # k_number is optional (blank=True in model), so not tested here

    def test_registration_short_password(self):
        """Test registration with password shorter than 8 characters"""
        data = self.valid_registration_data.copy()
        data['password'] = 'short'
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_invalid_email(self):
        """Test registration with invalid email format"""
        data = self.valid_registration_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserMeViewTest(TestCase):
    """Test cases for /users/me/ endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.me_url = '/api/users/me/'
        
        # Create test users
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            first_name='Student',
            last_name='User',
            role=User.Role.STUDENT
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

    def test_me_view_unauthenticated(self):
        """Test that unauthenticated users cannot access /users/me/"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_view_authenticated_student(self):
        """Test authenticated student user accessing /users/me/"""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'student')
        self.assertEqual(response.data['email'], 'student@test.com')
        self.assertEqual(response.data['role'], 'student')
        self.assertFalse(response.data['is_staff'])
        self.assertFalse(response.data['is_superuser'])

    def test_me_view_authenticated_admin(self):
        """Test authenticated admin user accessing /users/me/"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'admin')
        self.assertEqual(response.data['email'], 'admin@test.com')
        self.assertEqual(response.data['role'], 'admin')
        self.assertTrue(response.data['is_staff'])
        self.assertTrue(response.data['is_superuser'])

    def test_me_view_returns_correct_fields(self):
        """Test that /users/me/ returns all expected fields"""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.me_url)
        
        expected_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'k_number', 'department', 'role', 'is_staff', 'is_superuser'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_me_view_update_profile(self):
        """Test updating own profile via /users/me/"""
        self.client.force_authenticate(user=self.student)
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'department': 'Engineering'
        }
        
        response = self.client.patch(self.me_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['department'], 'Engineering')
        
        # Verify in database
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Updated')

    def test_me_view_cannot_change_role(self):
        """Test that users cannot change their own role via /users/me/"""
        self.client.force_authenticate(user=self.student)
        
        # Try to change role to admin
        response = self.client.patch(self.me_url, {'role': 'admin'})
        
        # Should succeed but role should be in read_only_fields
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.Role.STUDENT)  # Unchanged

    def test_me_view_with_jwt_token(self):
        """Test /users/me/ with JWT token authentication"""
        # Get JWT token
        token_response = self.client.post('/api/auth/token/', {
            'username': 'student',
            'password': 'testpass123'
        })
        access_token = token_response.data['access']
        
        # Use token in Authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'student')


class IntegrationLoginFlowTest(TestCase):
    """Integration test for complete login flow"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

    def test_complete_admin_login_flow(self):
        """Test complete flow: login → get token → access protected endpoint"""
        # Step 1: Login and get tokens
        login_response = self.client.post('/api/auth/token/', {
            'username': 'admin',
            'password': 'adminpass123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        
        # Step 2: Use token to access /users/me/
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_response = self.client.get('/api/users/me/')
        
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'admin')
        self.assertTrue(me_response.data['is_superuser'])
        
        # Step 3: Access admin dashboard endpoint
        dashboard_response = self.client.get('/api/admin/dashboard/stats/')
        
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', dashboard_response.data)

    def test_complete_registration_login_flow(self):
        """Test complete flow: register → login → access profile"""
        # Step 1: Register new user
        register_response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'k_number': '12345678',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Login with new credentials
        login_response = self.client.post('/api/auth/token/', {
            'username': 'newuser',
            'password': 'newpass123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        
        # Step 3: Access own profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_response = self.client.get('/api/users/me/')
        
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'newuser')
        self.assertEqual(me_response.data['role'], 'student')
