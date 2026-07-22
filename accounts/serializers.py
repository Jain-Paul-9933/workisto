"""
Serializers for the accounts API.

Three concerns, deliberately kept separate:
- `UserSerializer`     — the *public* shape of a user (what /api/me/ returns).
                         Never carries the password, in or out.
- `RegisterSerializer` — self-service signup. Constrains `role` to CUSTOMER or
                         PROVIDER; ADMIN is created only via `createsuperuser`.
- `LoginSerializer`    — validates credentials; the view turns the returned user
                         into a session.
"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "first_name", "last_name"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    # write_only: accepted on input, never echoed back. validate_password runs
    # Django's configured password validators (length, common, numeric, ...).
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"},
        validators=[validate_password],
    )
    # The security-critical line: a client can sign up as a customer or a
    # provider, but NOT mint themselves an admin.
    role = serializers.ChoiceField(
        choices=[User.Role.CUSTOMER, User.Role.PROVIDER],
        default=User.Role.CUSTOMER,
    )

    class Meta:
        model = User
        fields = ["id", "email", "password", "role", "first_name", "last_name"]

    def create(self, validated_data):
        # create_user hashes the password; never store it raw.
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"},
    )

    def validate(self, attrs):
        # USERNAME_FIELD is email, so the ModelBackend looks the user up by it.
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            # One vague message for both "no such email" and "wrong password" —
            # don't leak which emails are registered.
            raise serializers.ValidationError(
                "Invalid email or password.", code="authorization",
            )
        attrs["user"] = user
        return attrs
