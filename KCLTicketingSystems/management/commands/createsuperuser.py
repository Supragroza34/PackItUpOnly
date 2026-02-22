from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Create a superuser with admin role (no k_number required for admins)'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--k_number',
            dest='k_number',
            default='',
            help='K number for the user (leave empty for admin users)',
        )

    def handle(self, *args, **options):
        from KCLTicketingSystems.models.user import User
        from django.utils import timezone
        from datetime import timedelta
        
        # Store k_number and remove from options before calling parent
        k_number = options.pop('k_number', '')
        
        # Get count of superusers before creating new one
        superuser_count_before = User.objects.filter(is_superuser=True).count()
        
        # Call the parent command to create the superuser
        super().handle(*args, **options)
        
        # Get the newly created superuser (most recent one)
        # Look for superusers created in the last minute
        recent_time = timezone.now() - timedelta(minutes=1)
        new_user = User.objects.filter(
            is_superuser=True,
            date_joined__gte=recent_time
        ).order_by('-date_joined').first()
        
        # Fallback: if no recent user found, get the most recent superuser
        if not new_user:
            new_user = User.objects.filter(is_superuser=True).order_by('-date_joined').first()
        
        if new_user:
            # Set role to admin and ensure k_number is empty (admins don't have k_numbers)
            new_user.role = User.Role.ADMIN
            new_user.k_number = k_number  # Empty string for admins
            new_user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{new_user.username}" with admin role')
            )
