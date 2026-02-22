import random
import string
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers

from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.core.throttles import AuthRateThrottle, ForgotPasswordThrottle

from .models import PasswordResetCode, RefreshTokenRecord, User
from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)


def _build_token_response(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role

    # Store hashed refresh token
    RefreshTokenRecord.objects.create(
        user=user,
        token_hash=RefreshTokenRecord.hash_token(str(refresh)),
        expires_at=timezone.now() + timedelta(days=30),
    )

    return {
        'accessToken': str(refresh.access_token),
        'refreshToken': str(refresh),
        'expiresIn': 3600,
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        tags=['Auth'],
        summary='Register a new user',
        description=(
            'Create a new user account with phone number as the primary identifier. '
            'Returns the created user profile along with JWT access and refresh tokens.'
        ),
        request=RegisterSerializer,
        responses={
            201: inline_serializer(
                name='RegisterResponse',
                fields={
                    'data': drf_serializers.DictField(
                        help_text='Wrapper containing user and tokens.',
                    ),
                },
            ),
            409: inline_serializer(
                name='RegisterConflictError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Conflict error when phone or email is already registered.',
                    ),
                },
            ),
            422: inline_serializer(
                name='RegisterValidationError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Validation error with field-level details.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Registration request',
                request_only=True,
                value={
                    'firstName': 'Amadou',
                    'lastName': 'Diallo',
                    'phone': '+2250700000001',
                    'email': 'amadou@example.com',
                    'password': 'SecurePass1',
                    'dateOfBirth': '1995-06-15',
                    'city': 'Abidjan',
                    'country': 'CI',
                },
            ),
            OpenApiExample(
                name='Registration success',
                response_only=True,
                status_codes=['201'],
                value={
                    'data': {
                        'user': {
                            'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                            'firstName': 'Amadou',
                            'lastName': 'Diallo',
                            'phone': '+2250700000001',
                            'email': 'amadou@example.com',
                            'dateOfBirth': '1995-06-15',
                            'city': 'Abidjan',
                            'country': 'CI',
                            'avatarUrl': None,
                            'createdAt': '2026-02-22T10:00:00Z',
                        },
                        'tokens': {
                            'accessToken': 'eyJhbGciOiJIUzI1NiIs...',
                            'refreshToken': 'eyJhbGciOiJIUzI1NiIs...',
                            'expiresIn': 3600,
                        },
                    }
                },
            ),
            OpenApiExample(
                name='Phone already registered',
                response_only=True,
                status_codes=['409'],
                value={
                    'error': {
                        'code': 'CONFLICT',
                        'message': 'Phone number already registered.',
                    }
                },
            ),
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            details = []
            for field, messages in serializer.errors.items():
                for msg in messages:
                    if 'already registered' in str(msg):
                        raise ConflictError(str(msg))
                    details.append({'field': field, 'message': str(msg)})
            raise ValidationError('Validation failed.', details)

        data = serializer.validated_data
        user = User.objects.create_user(
            phone=data['phone'],
            password=data['password'],
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data.get('email') or None,
            date_of_birth=data.get('dateOfBirth'),
            city=data.get('city'),
            country=data.get('country'),
        )

        tokens = _build_token_response(user)
        user_data = UserSerializer(user).data

        return Response({
            'data': {
                'user': user_data,
                'tokens': tokens,
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        tags=['Auth'],
        summary='Authenticate a user',
        description=(
            'Authenticate with phone number and password. '
            'Returns the user profile and JWT access/refresh token pair on success.'
        ),
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name='LoginResponse',
                fields={
                    'data': drf_serializers.DictField(
                        help_text='Wrapper containing user and tokens.',
                    ),
                },
            ),
            401: inline_serializer(
                name='LoginUnauthorizedError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Invalid credentials error.',
                    ),
                },
            ),
            422: inline_serializer(
                name='LoginValidationError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Validation error with field-level details.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Login request',
                request_only=True,
                value={
                    'phone': '+2250700000001',
                    'password': 'SecurePass1',
                },
            ),
            OpenApiExample(
                name='Login success',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'user': {
                            'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                            'firstName': 'Amadou',
                            'lastName': 'Diallo',
                            'phone': '+2250700000001',
                            'email': 'amadou@example.com',
                            'dateOfBirth': '1995-06-15',
                            'city': 'Abidjan',
                            'country': 'CI',
                            'avatarUrl': None,
                            'createdAt': '2026-02-22T10:00:00Z',
                        },
                        'tokens': {
                            'accessToken': 'eyJhbGciOiJIUzI1NiIs...',
                            'refreshToken': 'eyJhbGciOiJIUzI1NiIs...',
                            'expiresIn': 3600,
                        },
                    }
                },
            ),
            OpenApiExample(
                name='Invalid credentials',
                response_only=True,
                status_codes=['401'],
                value={
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Invalid phone/password combination.',
                    }
                },
            ),
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Missing required fields.', details)

        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Invalid phone/password combination.',
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Invalid phone/password combination.',
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        tokens = _build_token_response(user)
        user_data = UserSerializer(user).data

        return Response({
            'data': {
                'user': user_data,
                'tokens': tokens,
            }
        })


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        summary='Refresh an access token',
        description=(
            'Exchange a valid refresh token for a new access/refresh token pair. '
            'The old refresh token is revoked upon successful rotation.'
        ),
        request=RefreshTokenSerializer,
        responses={
            200: inline_serializer(
                name='RefreshTokenResponse',
                fields={
                    'data': inline_serializer(
                        name='TokenPair',
                        fields={
                            'accessToken': drf_serializers.CharField(),
                            'refreshToken': drf_serializers.CharField(),
                            'expiresIn': drf_serializers.IntegerField(),
                        },
                    ),
                },
            ),
            401: inline_serializer(
                name='RefreshUnauthorizedError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Token expired, revoked, or invalid.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Refresh request',
                request_only=True,
                value={
                    'refreshToken': 'eyJhbGciOiJIUzI1NiIs...',
                },
            ),
            OpenApiExample(
                name='Refresh success',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'accessToken': 'eyJhbGciOiJIUzI1NiIs...',
                        'refreshToken': 'eyJhbGciOiJIUzI1NiIs...',
                        'expiresIn': 3600,
                    }
                },
            ),
            OpenApiExample(
                name='Expired refresh token',
                response_only=True,
                status_codes=['401'],
                value={
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Refresh token expired or invalid.',
                    }
                },
            ),
        ],
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': {'code': 'UNAUTHORIZED', 'message': 'Refresh token is required.'}
            }, status=status.HTTP_401_UNAUTHORIZED)

        raw_token = serializer.validated_data['refreshToken']
        token_hash = RefreshTokenRecord.hash_token(raw_token)

        record = RefreshTokenRecord.objects.filter(
            token_hash=token_hash,
            is_revoked=False,
            expires_at__gt=timezone.now(),
        ).first()

        if not record:
            return Response({
                'error': {'code': 'UNAUTHORIZED', 'message': 'Refresh token expired or invalid.'}
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Revoke old token
        record.is_revoked = True
        record.save()

        try:
            old_refresh = RefreshToken(raw_token)
            user = User.objects.get(id=old_refresh['sub'])
        except Exception:
            return Response({
                'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid refresh token.'}
            }, status=status.HTTP_401_UNAUTHORIZED)

        tokens = _build_token_response(user)

        return Response({
            'data': tokens
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Log out the current user',
        description=(
            'Revoke the provided refresh token to end the user session. '
            'The access token remains valid until expiry but no new tokens '
            'can be obtained with the revoked refresh token. '
            'Returns 204 regardless of whether the token was found.'
        ),
        request=RefreshTokenSerializer,
        responses={
            204: None,
        },
        examples=[
            OpenApiExample(
                name='Logout request',
                request_only=True,
                value={
                    'refreshToken': 'eyJhbGciOiJIUzI1NiIs...',
                },
            ),
        ],
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            raw_token = serializer.validated_data['refreshToken']
            token_hash = RefreshTokenRecord.hash_token(raw_token)
            RefreshTokenRecord.objects.filter(token_hash=token_hash).update(is_revoked=True)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ForgotPasswordThrottle]

    @extend_schema(
        tags=['Auth'],
        summary='Request a password reset code',
        description=(
            'Send a 6-digit password reset code via SMS to the given phone number. '
            'Always returns 200 regardless of whether the phone exists to prevent '
            'user enumeration. The code expires after 10 minutes.'
        ),
        request=ForgotPasswordSerializer,
        responses={
            200: inline_serializer(
                name='ForgotPasswordResponse',
                fields={
                    'data': inline_serializer(
                        name='ForgotPasswordData',
                        fields={
                            'message': drf_serializers.CharField(),
                            'expiresIn': drf_serializers.IntegerField(
                                help_text='Code validity duration in seconds.',
                            ),
                        },
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Forgot password request',
                request_only=True,
                value={
                    'phone': '+2250700000001',
                },
            ),
            OpenApiExample(
                name='Forgot password success',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'message': 'Un code de reinitialisation a ete envoye par SMS.',
                        'expiresIn': 600,
                    }
                },
            ),
        ],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']

        # Always return 200 to prevent enumeration
        response_data = {
            'data': {
                'message': 'Un code de reinitialisation a ete envoye par SMS.',
                'expiresIn': 600,
            }
        }

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(response_data)

        # Generate 6-digit code
        code = ''.join(random.choices(string.digits, k=6))

        # Invalidate old codes
        PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

        PasswordResetCode.objects.create(
            user=user,
            code_hash=PasswordResetCode.hash_code(code),
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        # In production: send SMS here
        # For dev: log the code
        print(f'[DEV] Password reset code for {phone}: {code}')

        return Response(response_data)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        summary='Reset password with verification code',
        description=(
            'Reset the user password using a 6-digit code previously sent via SMS. '
            'The code must not be expired or already used. On success the password '
            'is updated and the code is consumed.'
        ),
        request=ResetPasswordSerializer,
        responses={
            200: inline_serializer(
                name='ResetPasswordResponse',
                fields={
                    'data': inline_serializer(
                        name='ResetPasswordData',
                        fields={
                            'message': drf_serializers.CharField(),
                        },
                    ),
                },
            ),
            422: inline_serializer(
                name='ResetPasswordValidationError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Validation error for invalid or expired code.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Reset password request',
                request_only=True,
                value={
                    'phone': '+2250700000001',
                    'code': '483921',
                    'newPassword': 'NewSecure1',
                },
            ),
            OpenApiExample(
                name='Reset password success',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'message': 'Mot de passe reinitialise avec succes.',
                    }
                },
            ),
            OpenApiExample(
                name='Invalid or expired code',
                response_only=True,
                status_codes=['422'],
                value={
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Code expired or invalid.',
                    }
                },
            ),
        ],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Validation failed.', details)

        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['newPassword']

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise ValidationError('Invalid reset code.')

        code_hash = PasswordResetCode.hash_code(code)
        reset_record = PasswordResetCode.objects.filter(
            user=user,
            code_hash=code_hash,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).first()

        if not reset_record:
            raise ValidationError('Code expired or invalid.')

        reset_record.is_used = True
        reset_record.save()

        user.set_password(new_password)
        user.save()

        return Response({
            'data': {
                'message': 'Mot de passe reinitialise avec succes.'
            }
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Users'],
        summary='Get current user profile',
        description='Return the full profile of the currently authenticated user.',
        responses={
            200: UserSerializer,
            401: inline_serializer(
                name='ProfileUnauthorizedError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Authentication credentials were not provided.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Profile response',
                response_only=True,
                status_codes=['200'],
                value={
                    'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                    'firstName': 'Amadou',
                    'lastName': 'Diallo',
                    'phone': '+2250700000001',
                    'email': 'amadou@example.com',
                    'dateOfBirth': '1995-06-15',
                    'city': 'Abidjan',
                    'country': 'CI',
                    'avatarUrl': None,
                    'createdAt': '2026-02-22T10:00:00Z',
                },
            ),
        ],
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        tags=['Users'],
        summary='Update current user profile',
        description=(
            'Partially update the authenticated user profile. Only the fields '
            'included in the request body are modified. Phone number cannot be changed.'
        ),
        request=ProfileUpdateSerializer,
        responses={
            200: UserSerializer,
            409: inline_serializer(
                name='ProfileConflictError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Conflict when the new email is already in use.',
                    ),
                },
            ),
            422: inline_serializer(
                name='ProfileValidationError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Validation error with field-level details.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Update profile request',
                request_only=True,
                value={
                    'firstName': 'Amadou',
                    'city': 'Bouake',
                },
            ),
            OpenApiExample(
                name='Update profile response',
                response_only=True,
                status_codes=['200'],
                value={
                    'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                    'firstName': 'Amadou',
                    'lastName': 'Diallo',
                    'phone': '+2250700000001',
                    'email': 'amadou@example.com',
                    'dateOfBirth': '1995-06-15',
                    'city': 'Bouake',
                    'country': 'CI',
                    'avatarUrl': None,
                    'createdAt': '2026-02-22T10:00:00Z',
                },
            ),
            OpenApiExample(
                name='Email conflict',
                response_only=True,
                status_codes=['409'],
                value={
                    'error': {
                        'code': 'CONFLICT',
                        'message': 'Email already in use by another account.',
                    }
                },
            ),
        ],
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Validation failed.', details)

        data = serializer.validated_data
        user = request.user

        field_map = {
            'firstName': 'first_name',
            'lastName': 'last_name',
            'email': 'email',
            'dateOfBirth': 'date_of_birth',
            'city': 'city',
            'country': 'country',
            'avatarUrl': 'avatar_url',
        }

        for api_field, model_field in field_map.items():
            if api_field in data:
                value = data[api_field]
                if api_field == 'email' and value:
                    if User.objects.filter(email=value).exclude(id=user.id).exists():
                        raise ConflictError('Email already in use by another account.')
                setattr(user, model_field, value)

        user.save()
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Users'],
        summary='Change the current user password',
        description=(
            'Change the password of the authenticated user. '
            'Requires the current password for verification and a new password '
            'that meets strength requirements (8+ chars, uppercase, digit).'
        ),
        request=ChangePasswordSerializer,
        responses={
            200: inline_serializer(
                name='ChangePasswordResponse',
                fields={
                    'data': inline_serializer(
                        name='ChangePasswordData',
                        fields={
                            'message': drf_serializers.CharField(),
                        },
                    ),
                },
            ),
            401: inline_serializer(
                name='ChangePasswordUnauthorizedError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Current password is incorrect.',
                    ),
                },
            ),
            422: inline_serializer(
                name='ChangePasswordValidationError',
                fields={
                    'error': drf_serializers.DictField(
                        help_text='Validation error with field-level details.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Change password request',
                request_only=True,
                value={
                    'currentPassword': 'OldSecure1',
                    'newPassword': 'NewSecure1',
                },
            ),
            OpenApiExample(
                name='Change password success',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'message': 'Mot de passe modifie avec succes.',
                    }
                },
            ),
            OpenApiExample(
                name='Wrong current password',
                response_only=True,
                status_codes=['401'],
                value={
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Current password incorrect.',
                    }
                },
            ),
        ],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Validation failed.', details)

        user = request.user
        if not user.check_password(serializer.validated_data['currentPassword']):
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Current password incorrect.',
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        user.set_password(serializer.validated_data['newPassword'])
        user.save()

        return Response({
            'data': {
                'message': 'Mot de passe modifie avec succes.'
            }
        })
