"""
Quick script to create an admin user for the KCL Ticketing System
Run this after creating a superuser with: python manage.py createsuperuser
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KCLTicketingSystem.settings')
django.setup()

from KCLTicketingSystems.models.user import User

def create_admin_user():
    print("=" * 50)
    print("KCL Ticketing System - Create Admin User")
    print("=" * 50)
    
    username = input("\nEnter username for admin: ").strip()
    
    if not username:
        print("❌ Username cannot be empty!")
        return
    
    # Check if user exists
    try:
        user = User.objects.get(username=username)
        print(f"\n✅ Found user: {user.username}")
        print(f"   Current role: {user.role}")
        
        confirm = input(f"\nChange {user.username}'s role to ADMIN? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            user.role = User.Role.ADMIN
            user.save()
            print(f"\n🎉 Success! {user.username} is now an ADMIN")
            print(f"\nYou can now login to the admin dashboard at:")
            print(f"   http://localhost:3000/admin/login")
            print(f"\n   Username: {user.username}")
            print(f"   Password: (the password you set)")
        else:
            print("\n❌ Operation cancelled")
    
    except User.DoesNotExist:
        print(f"\n❌ User '{username}' not found!")
        print("\nPlease create the user first with:")
        print("   python manage.py createsuperuser")
        print("\nThen run this script again.")

if __name__ == '__main__':
    create_admin_user()
