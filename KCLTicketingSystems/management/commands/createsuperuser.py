from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Create a superuser with admin role'

    def handle(self, *args, **options):
        # Call the parent command to create the superuser
        super().handle(*args, **options)
        
        # Get the username from options
        username = options.get('username')
        if not username:
            # If interactive mode, get the username from database_username
            username = options.get('database')
        
        # If we still don't have username, try to get the last created superuser
        from KCLTicketingSystems.models.user import User
        
        if username:
            try:
                user = User.objects.get(username=username)
                if user.is_superuser and user.role != User.Role.ADMIN:
                    user.role = User.Role.ADMIN
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully set role to "admin" for superuser: {username}')
                    )
            except User.DoesNotExist:
                pass
        else:
            # Fallback: update all superusers without admin role
            superusers = User.objects.filter(is_superuser=True).exclude(role=User.Role.ADMIN)
            if superusers.exists():
                count = superusers.update(role=User.Role.ADMIN)
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {count} superuser(s) to have admin role')
                )
