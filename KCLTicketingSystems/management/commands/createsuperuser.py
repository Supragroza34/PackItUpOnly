from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Create a superuser with admin role'

    def _update_user_role(self, username):
        """Update a specific user's role to admin."""
        from KCLTicketingSystems.models.user import User
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

    def _update_all_superusers(self):
        """Update all superusers without admin role."""
        from KCLTicketingSystems.models.user import User
        superusers = User.objects.filter(is_superuser=True).exclude(role=User.Role.ADMIN)
        if superusers.exists():
            count = superusers.update(role=User.Role.ADMIN)
            self.stdout.write(
                self.style.SUCCESS(f'Updated {count} superuser(s) to have admin role')
            )

    def handle(self, *args, **options):
        super().handle(*args, **options)
        username = options.get('username') or options.get('database')
        from KCLTicketingSystems.models.user import User
        if username:
            self._update_user_role(username)
        else:
            self._update_all_superusers()
