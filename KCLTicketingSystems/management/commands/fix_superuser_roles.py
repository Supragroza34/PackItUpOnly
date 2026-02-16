from django.core.management.base import BaseCommand
from KCLTicketingSystems.models.user import User


class Command(BaseCommand):
    help = 'Update all superusers to have admin role'

    def handle(self, *args, **options):
        # Find all superusers without admin role
        superusers = User.objects.filter(is_superuser=True).exclude(role=User.Role.ADMIN)
        
        if not superusers.exists():
            self.stdout.write(
                self.style.SUCCESS('All superusers already have admin role!')
            )
            return
        
        # Update them
        for user in superusers:
            old_role = user.role
            user.role = User.Role.ADMIN
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {user.username}: {old_role} -> admin'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal updated: {superusers.count()} superuser(s)')
        )
