# Create a management command to create admin user
# accounts/management/commands/create_admin.py

import os
import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create admin user'
    
    def handle(self, *args, **options):
        email = input("Enter admin email: ")
        username = input("Enter admin username: ")
        password = input("Enter admin password: ")
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR('User with this email already exists'))
            return
        
        admin = User.objects.create_superuser(
            email=email,
            username=username,
            password=password
        )
        admin.role = 'super_admin'
        admin.save()
        
        self.stdout.write(self.style.SUCCESS(f'Admin user {email} created successfully'))