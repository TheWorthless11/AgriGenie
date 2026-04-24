from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superadmin user for AgriGenie'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Admin username (default: admin)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Admin password (default: admin123)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@agrigenie.local',
            help='Admin email (default: admin@agrigenie.local)'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Admin user "{username}" already exists. Skipping creation.'
                    )
                )
                return

            # Create superuser with admin role
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='admin'
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Superadmin user "{username}" created successfully!'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Login URL: http://127.0.0.1:8000/admin/'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Username: {username}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Email: {email}'
                )
            )

        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error creating superadmin: {str(e)}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Unexpected error: {str(e)}'
                )
            )
