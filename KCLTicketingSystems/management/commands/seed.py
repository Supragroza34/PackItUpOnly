"""
Management command to seed the database with demo data.

This command creates a small set of named fixture users and then fills up
to ``USER_COUNT`` total users using Faker-generated data. Existing records
are left untouched—if a create fails (e.g., due to duplicates), the error
is swallowed and generation continues.
"""


from faker import Faker
from faker.providers import job
from random import randint, random
from django.core.management.base import BaseCommand, CommandError
from ...models import User

user_fixtures = [
    {'username': 'johndoe', 'email': 'john.doe@example.org', 'k_number': '12345678', 'first_name': 'John', 'last_name': 'Doe', 'department': 'Informatics', 'role': 'student'},
    {'username': 'janedee', 'email': 'jane.dee@example.org', 'k_number': '45678123', 'first_name': 'Jane', 'last_name': 'Dee', 'department': 'Informatics', 'role': 'staff'},
    {'username': 'Chrisdoo', 'email': 'chris.doo@example.org', 'k_number': '03472783', 'first_name': 'Chris', 'last_name': 'Doo', 'department': 'Informatics', 'role': 'student'},
]


class Command(BaseCommand):
    """
    Build automation command to seed the database with data.

    This command inserts a small set of known users (``user_fixtures``) and then
    repeatedly generates additional random users until ``USER_COUNT`` total users
    exist in the database. Each generated user receives the same default password.

    Attributes:
        USER_COUNT (int): Target total number of users in the database.
        DEFAULT_PASSWORD (str): Default password assigned to all created users.
        help (str): Short description shown in ``manage.py help``.
        faker (Faker): Locale-specific Faker instance used for random data.
    """

    STUDENT_COUNT = 100
    STAFF_COUNT = 100
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self, *args, **kwargs):
        """Initialize the command with a locale-specific Faker instance."""
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')
        self.faker.add_provider(job.Provider)

    def handle(self, *args, **options):
        """
        Django entrypoint for the command.

        Runs the full seeding workflow and stores ``self.users`` for any
        post-processing or debugging (not required for operation).
        """
        User.objects.create_superuser('spr_usr', 'spr.usr@example.org', 'SuperUser8^]')
        self.create_users()
        self.users = User.objects.all()

    def create_users(self):
        """
        Create fixture users and then generate random users up to USER_COUNT.

        The process is idempotent in spirit: attempts that fail (e.g., due to
        uniqueness constraints on username/email) are ignored and generation continues.
        """
        self.generate_user_fixtures()
        self.generate_random_students()
        self.generate_random_staff()

    def generate_user_fixtures(self):
        """Attempt to create each predefined fixture user."""
        for data in user_fixtures:
            self.try_create_user(data)
        print("Fixture seeding complete.        ")    

    def generate_random_students(self):
        """
        Generate random users until the database contains USER_COUNT users.

        Prints a simple progress indicator to stdout during generation.
        """
        user_count = User.objects.count()
        while  user_count < self.STUDENT_COUNT:
            print(f"Seeding student {user_count}/{self.STUDENT_COUNT}", end='\r')
            self.generate_student()
            user_count = User.objects.count()
        print("Student seeding complete.      ")

    def generate_random_staff(self):
        """
        Generate random users until the database contains USER_COUNT users.

        Prints a simple progress indicator to stdout during generation.
        """
        user_count = User.objects.count()
        while  user_count < self.STAFF_COUNT*2:
            print(f"Seeding staff {user_count}/{self.STAFF_COUNT}", end='\r')
            self.generate_staff()
            user_count = User.objects.count()
        print("Staff seeding complete.      ")        

    def generate_student(self):
        """
        Generate a single random user and attempt to insert it.

        Uses Faker for first/last names, then derives a simple username/email.
        """
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        k_number = str(self.faker.random_number(digits=8, fix_len = True))
        username = create_username(k_number)
        email = create_email(k_number)
        department = self.faker.job()
        role = "Student"
        self.try_create_user({'username': username, 'email': email, 'k_number': k_number, 'department': department, 'role': role, 'first_name':first_name, 'last_name': last_name})

    def generate_staff(self):

        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        k_number = str(self.faker.random_number(digits=8, fix_len = True))
        username = create_username(k_number)
        email = create_email(k_number)
        department = self.faker.job()
        role = "Staff"
        self.try_create_user({'username': username, 'email': email, 'k_number': k_number, 'department': department, 'role': role, 'first_name':first_name, 'last_name': last_name})
       
    def try_create_user(self, data):
        """
        Attempt to create a user and ignore any errors.

        Args:
            data (dict): Mapping with keys ``username``, ``email``,
                ``first_name``, and ``last_name``.
        """
        try:
            self.create_user(data)
        except:
            print("did not create user " + data['first_name'])

    def create_user(self, data):
        """
        Create a user with the default password.

        Args:
            data (dict): Mapping with keys ``username``, ``email``,
                ``first_name``, and ``last_name``.
        """
        User.objects.create(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            k_number=data['k_number'],
            department=data['department'],
            role=data['role'],
            password=Command.DEFAULT_PASSWORD,
        )

def create_username(k_number):
    """
    Construct a simple username from first and last names.

    Args:
        first_name (str): Given name.
        last_name (str): Family name.

    Returns:
        str: A username in the form ``@{firstname}{lastname}`` (lowercased).
    """
    return '@' + k_number

def create_email(k_number):
    """
    Construct a simple example email address.

    Args:
        k_number (str): K number without k

    Returns:
        str: An email in the form ``k{k_number}@kcl.ac.uk``.
    """
    return 'k' + k_number + '@kcl.ac.uk'
