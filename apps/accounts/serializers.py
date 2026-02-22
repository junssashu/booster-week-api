import re

from rest_framework import serializers

from .models import User


def validate_password_strength(password):
    if len(password) < 8:
        raise serializers.ValidationError('Password must be at least 8 characters.')
    if not re.search(r'[A-Z]', password):
        raise serializers.ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'\d', password):
        raise serializers.ValidationError('Password must contain at least one digit.')
    return password


class RegisterSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=100)
    lastName = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(write_only=True)
    dateOfBirth = serializers.DateField(required=False, allow_null=True)
    city = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('Phone number already registered.')
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()


class RefreshTokenSerializer(serializers.Serializer):
    refreshToken = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    newPassword = serializers.CharField()

    def validate_newPassword(self, value):
        return validate_password_strength(value)


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField()
    newPassword = serializers.CharField()

    def validate_newPassword(self, value):
        return validate_password_strength(value)


class UserSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    dateOfBirth = serializers.DateField(source='date_of_birth', allow_null=True, required=False)
    avatarUrl = serializers.URLField(source='avatar_url', allow_null=True, required=False)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'firstName', 'lastName', 'phone', 'email',
                  'dateOfBirth', 'city', 'country', 'avatarUrl', 'createdAt']
        read_only_fields = ['id', 'phone', 'createdAt']


class ProfileUpdateSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=100, required=False)
    lastName = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False, allow_null=True)
    dateOfBirth = serializers.DateField(required=False, allow_null=True)
    city = serializers.CharField(max_length=100, required=False, allow_null=True)
    country = serializers.CharField(max_length=100, required=False, allow_null=True)
    avatarUrl = serializers.URLField(required=False, allow_null=True)
