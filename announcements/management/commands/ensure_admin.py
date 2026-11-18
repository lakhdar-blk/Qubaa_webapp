"""Create or update the mosque administrator from environment variables.

Used automatically by build.sh on Render, so the first deployment has a
working admin account without manual shell access.
"""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


def env_flag(name):
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Create the initial superuser from ADMIN_EMAIL and ADMIN_PASSWORD."

    def add_arguments(self, parser):
        parser.add_argument("--email", default=None)
        parser.add_argument("--password", default=None)
        parser.add_argument("--name", default=None)
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Reset the password of an existing account.",
        )

    def handle(self, *args, **options):
        email = (options["email"] or os.getenv("ADMIN_EMAIL", "")).strip().lower()
        password = options["password"] or os.getenv("ADMIN_PASSWORD", "")
        name = options["name"] or os.getenv("ADMIN_NAME", "Administrator")
        reset_password = options["reset_password"] or env_flag(
            "ADMIN_RESET_PASSWORD"
        )

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "ADMIN_EMAIL / ADMIN_PASSWORD are not set — skipping admin creation."
                )
            )
            return

        User = get_user_model()
        user = User.objects.filter(username__iexact=email).first()
        if user is None:
            user = User.objects.filter(email__iexact=email).first()

        created = user is None
        if created:
            user = User(username=email, email=email)
        else:
            # Keep the existing username if an account was found by email.
            if not user.username:
                user.username = email
            user.email = email

        user.is_staff = True
        user.is_superuser = True
        user.is_active = True

        if name:
            parts = name.strip().split(" ", 1)
            user.first_name = parts[0][:150]
            user.last_name = (parts[1] if len(parts) > 1 else "")[:150]

        if created or reset_password:
            try:
                validate_password(password, user=user)
            except ValidationError as error:
                raise CommandError(
                    "The administrator password is too weak: "
                    + " ".join(error.messages)
                ) from error
            user.set_password(password)

        user.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Administrator account created: {email}"
                )
            )
        else:
            action = "password reset" if reset_password else "account updated"
            self.stdout.write(
                self.style.SUCCESS(f"Administrator {email}: {action}.")
            )
