"""
Management command to seed the database with demo data.

This command creates a small set of named fixture users and then fills up
to ``USER_COUNT`` total users using Faker-generated data. Existing records
are left untouched—if a create fails (e.g., due to duplicates), the error
is swallowed and generation continues.
"""


from faker import Faker
from random import randint, random, choice
from django.core.management.base import BaseCommand, CommandError
from ...models import User, Ticket, OfficeHours
from datetime import time
from ...services import staff_selection

user_fixtures = [
    {'username': 'johndoe', 'email': 'john.doe@example.org', 'k_number': '12345678', 'first_name': 'John', 'last_name': 'Doe', 'department': 'Informatics', 'role': 'student'},
    {'username': 'janedee', 'email': 'jane.dee@example.org', 'k_number': '45678123', 'first_name': 'Jane', 'last_name': 'Dee', 'department': 'Informatics', 'role': 'staff'},
    {'username': 'Chrisdoo', 'email': 'chris.doo@example.org', 'k_number': '03472783', 'first_name': 'Chris', 'last_name': 'Doo', 'department': 'Informatics', 'role': 'student'},
    {'username': 'alexadmin', 'email': 'alex.admin@example.org', 'k_number': '', 'first_name': '', 'last_name': '', 'department': '', 'role': 'admin'},
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
    This keeps operational tasks repeatable and auditable.
    """

    TICKET_COUNT_PER_STUDENT = 5
    STUDENT_COUNT = 100
    STAFF_COUNT = 100
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self, *args, **kwargs):
        """Initialize the command with a locale-specific Faker instance. This keeps operational tasks repeatable and auditable."""
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        """
        Django entrypoint for the command.

        Runs the full seeding workflow and stores ``self.users`` for any
        post-processing or debugging (not required for operation).
        This keeps operational tasks repeatable and auditable.
        """
        # Try to create superuser if it doesn't exist
        try:
            if not User.objects.filter(username='spr_usr').exists():
                spr_user = User.objects.create_superuser(
                    username='spr_usr',
                    email='spr.usr@example.org',
                    password='SuperUser8^]',
                    k_number=''  # Admins don't have k_numbers
                )
                spr_user.role = User.Role.ADMIN
                spr_user.save()
                print("Created superuser 'spr_usr'")
        except Exception as e:
            print(f"Superuser creation skipped: {e}")
        
        self.create_users()
        # Seed office hours for staff users so they have default availability
        try:
            self.seed_office_hours()
        except Exception as e:
            print(f"Seeding office hours skipped: {e}")

        self.users = User.objects.all()
        self.create_student_tickets()
        self.tickets = Ticket.objects.all()

    def get_random_department(self):

        """Support get random department steps so the command remains safe to run across environments."""
        departments = [
            "Informatics",
            "Engineering",
            "Medicine",
            "Law",
            "Finance",
            "Mathematics",
            "English",
            "Foreign Languages",
            "Arts and Music",
            "Media"
        ]

        return choice(departments)    

    def create_student_tickets(self):
        """
        Create some tickets for all generated students.
        This keeps operational tasks repeatable and auditable.
        """
        students = User.objects.filter(role="student")
        ticket_count = Ticket.objects.count()
        for student in students:
            print(f"Seeding ticket {ticket_count}/{self.STUDENT_COUNT * self.TICKET_COUNT_PER_STUDENT}", end='\r')
            self.generate_n_tickets(self.TICKET_COUNT_PER_STUDENT, student)
            ticket_count = Ticket.objects.count()  
        
        print("Ticket seeding complete.        ")                 

    def create_users(self):
        """
        Create fixture users and then generate random users up to USER_COUNT.

        The process is idempotent in spirit: attempts that fail (e.g., due to
        uniqueness constraints on username/email) are ignored and generation continues.
        This keeps operational tasks repeatable and auditable.
        """
        self.generate_user_fixtures()
        self.generate_random_students()
        self.generate_random_staff()

    def generate_n_tickets(self, number_of_tickets, student):
        """Support generate n tickets steps so the command remains safe to run across environments."""
        for i in range(number_of_tickets):
            self.generate_one_ticket(student)

    def get_least_busy_staff(self, department):
        """Support get least busy staff steps so the command remains safe to run across environments."""
        staff_member = staff_selection.get_staff_with_least_tickets_in_department(department)
        return staff_member

    def generate_one_ticket(self, student):
        """Support generate one ticket steps so the command remains safe to run across environments."""
        department = self.get_random_department()
        issue = "Problem in the " + department + " department."
        staff_member_id = self.get_least_busy_staff(department)["id"]
        staff_member = User.objects.get(id=staff_member_id)
        additional_details = self.faker.sentence()
        ticket_data = {
            'user': student,
            'department': department,
            'type_of_issue': issue,
            'additional_details': additional_details,
            'assigned_to': staff_member,
        }
        self.try_create_ticket(ticket_data)   
    
    def generate_user_fixtures(self):
        """Attempt to create each predefined fixture user. This keeps operational tasks repeatable and auditable."""
        for data in user_fixtures:
            self.try_create_user(data)
        print("Fixture seeding complete.        ")    

    def generate_random_students(self):
        """
        Generate random users until the database contains USER_COUNT users.

        Prints a simple progress indicator to stdout during generation.
        This keeps operational tasks repeatable and auditable.
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
        This keeps operational tasks repeatable and auditable.
        """
        user_count = User.objects.count()-self.STUDENT_COUNT
        while  user_count < self.STAFF_COUNT:
            print(f"Seeding staff {user_count}/{self.STAFF_COUNT}", end='\r')
            self.generate_staff()
            user_count = User.objects.count()-self.STUDENT_COUNT
        print("Staff seeding complete.      ")        

    def generate_student(self):
        """
        Generate a single random user and attempt to insert it.

        Uses Faker for first/last names, then derives a simple username/email.
        This keeps operational tasks repeatable and auditable.
        """
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        k_number = str(self.faker.random_number(digits=8, fix_len = True))
        username = create_username(k_number)
        email = create_email(k_number)
        department = self.get_random_department()
        role = "student"
        self.try_create_user({'username': username, 'email': email, 'k_number': k_number, 'department': department, 'role': role, 'first_name':first_name, 'last_name': last_name})

    def generate_staff(self):

        """Support generate staff steps so the command remains safe to run across environments."""
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        staff_number = str(self.faker.random_number(digits=8, fix_len = True))
        username = create_staff_username(staff_number)
        email = create_staff_email(first_name, last_name)
        department = self.get_random_department()
        role = "staff"
        self.try_create_user({'username': username, 'email': email, 'k_number': staff_number, 'department': department, 'role': role, 'first_name':first_name, 'last_name': last_name})

    def try_create_ticket(self, data):
        """
        Attempt to create a ticket
        This keeps operational tasks repeatable and auditable.
        """
        try:
            self.create_ticket(data)
        except:
            print("did not create ticket")

    def create_ticket(self, data):
        """Support create ticket steps so the command remains safe to run across environments."""
        ticket = Ticket.objects.create(
            user=data['user'],
            department=data['department'],
            type_of_issue=data['type_of_issue'],
            additional_details=data['additional_details'],
            assigned_to=data['assigned_to']
        )
        ticket.save()

    def try_create_user(self, data):
        """
        Attempt to create a user and ignore any errors.

        Args:
            data (dict): Mapping with keys ``username``, ``email``,
                ``first_name``, and ``last_name``.
        This keeps operational tasks repeatable and auditable.
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
        This keeps operational tasks repeatable and auditable.
        """
        user = User.objects.create(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            k_number=data['k_number'],
            department=data['department'],
            role=data['role'],
        )
        # Set is_staff flag for staff and admin users
        if data['role'] in ['staff', 'admin']:
            user.is_staff = True
        user.set_password(Command.DEFAULT_PASSWORD)
        user.save()

    def seed_office_hours(self):
        """
        Create default office hours blocks for all staff users.
        Existing office hours for each staff user are removed first to
        make the seeding idempotent.
        This keeps operational tasks repeatable and auditable.
        """
        # single default template applied to all staff users (idempotent)
        default_template = [
            {"day_of_week": "Monday", "start_time": time(9, 0), "end_time": time(12, 0)},
            {"day_of_week": "Wednesday", "start_time": time(14, 0), "end_time": time(16, 0)},
            {"day_of_week": "Friday", "start_time": time(10, 0), "end_time": time(12, 0)},
        ]

        staff_qs = User.objects.filter(role=User.Role.STAFF)
        for staff in staff_qs:
            try:
                OfficeHours.objects.filter(staff=staff).delete()
                for b in default_template:
                    OfficeHours.objects.create(
                        staff=staff,
                        day_of_week=b["day_of_week"],
                        start_time=b["start_time"],
                        end_time=b["end_time"],
                    )
                print(f"Seeded office hours for {staff.username}")
            except Exception:
                # don't fail the entire seeding process for one user
                print(f"Could not seed office hours for {staff}")

def create_username(k_number):
    """
    Construct a simple username from first and last names.

    Args:
        first_name (str): Given name.
        last_name (str): Family name.

    Returns:
        str: A username in the form ``@{firstname}{lastname}`` (lowercased).
    This keeps operational tasks repeatable and auditable.
    """
    return '@' + k_number

def create_email(k_number):
    """
    Construct a simple example email address.

    Args:
        k_number (str): K number without k

    Returns:
        str: An email in the form ``k{k_number}@kcl.ac.uk``.
    This keeps operational tasks repeatable and auditable.
    """
    return 'k' + k_number + '@kcl.ac.uk'

def create_staff_username(staff_number):
    """
    Construct a staff username from department and staff_number.

    Args:
        staff_number (str):  random UNIQUE number.

    Returns:
        str: A username in the form ``Staff{staff_number}``.
    This keeps operational tasks repeatable and auditable.
    """
    return "Staff" + staff_number    

def create_staff_email(first_name, last_name):
    """
    Construct email address for staff.

    Args:
        staff_number (str): random UNIQUE number

    Returns:
        str: An email in the form ``Staff{staff_number}@kcl.ac.uk``.
    This keeps operational tasks repeatable and auditable.
    """
    return first_name.lower() + "." + last_name.lower() + '@kcl.ac.uk'