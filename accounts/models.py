"""
The custom User.

Two deliberate decisions worth defending in an interview:

1. ONE user table with a `role`, not separate Customer/Provider user tables.
   Auth (login, password, permissions) is identical for everyone; only the
   *profile* differs. So role lives here, and role-specific data lives in a
   separate profile model (ServiceProvider, built next increment) linked 1:1.

2. Login by EMAIL, not username. This is a marketplace — nobody wants a
   username. We drop `username` entirely and make `email` the identifier.
   Doing this NOW matters: switching the USERNAME_FIELD after the first
   migration is a genuinely painful change.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager for a User whose identifier is email, not username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        PROVIDER = "PROVIDER", "Provider"
        ADMIN = "ADMIN", "Admin"

    # Remove username; email is the login identifier.
    username = None
    email = models.EmailField("email address", unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password are already required by USERNAME_FIELD

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_provider(self):
        return self.role == self.Role.PROVIDER
