import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError


class Command(BaseCommand):
    help = """
    Initialize the application by running migrations and creating an admin user.
    
    This command will:
    1. Run makemigrations to generate any pending migrations
    2. Run migrate to apply migrations to the database
    3. Create an admin user with credentials from environment variables
    
    Required environment variables:
    - ADMIN_USERNAME: Username for the admin user
    - ADMIN_EMAIL: Email for the admin user  
    - ADMIN_PASSWORD: Password for the admin user
    
    Usage:
    python manage.py init
    python manage.py init --force  # Update existing user
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force creation even if user already exists (will update existing user)",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        # Get credentials from environment variables
        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")

        # Validate that credentials are provided
        if not all([username, email, password]):
            raise CommandError(
                "Admin credentials not found. Please set ADMIN_USERNAME, "
                "ADMIN_EMAIL, and ADMIN_PASSWORD in your .env file."
            )

        # Run database migrations first
        self.stdout.write("Running makemigrations...")
        try:
            call_command('makemigrations')
            self.stdout.write(self.style.SUCCESS("✓ makemigrations completed"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"makemigrations warning: {e}"))

        self.stdout.write("Running migrate...")
        try:
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS("✓ migrate completed"))
        except Exception as e:
            raise CommandError(f"Migration failed: {e}") from e

        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                if options["force"]:
                    user = User.objects.get(email=email)
                    user.username = username
                    user.email = email
                    user.set_password(password)
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_active = True
                    user.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully updated existing admin user: {email} \
                                (using credentials from environment variables)"
                        )
                    )
                else:
                    self.stdout.write(self.style.WARNING(f"User with email {email} already exists. Use --force to update."))
                    return
            else:
                # Create new superuser
                user = User.objects.create_superuser(
                    email=email,
                    password=password,
                    username=username,
                )
                user.is_active = True
                user.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created admin user: {email} (using credentials from environment variables)"
                    )
                )

        except IntegrityError as e:
            raise CommandError(f"Error creating admin user: {e}") from e
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}") from e

        self.stdout.write(
            self.style.SUCCESS(
                "Admin user details (from environment variables):\n"
                f"  Username: {username}\n"
                f"  Email: {email}\n"
                f"  Password: {'*' * len(password)} (hidden for security)\n"
                f"  Staff: Yes\n"
                f"  Superuser: Yes"
            )
        )
