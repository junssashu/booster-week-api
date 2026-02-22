from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class AppError(APIException):
    def __init__(self, code, message, details=None, status_code=400):
        self.code = code
        self.detail = {
            'error': {
                'code': code,
                'message': message,
            }
        }
        if details:
            self.detail['error']['details'] = details
        self.status_code = status_code


class ValidationError(AppError):
    def __init__(self, message='Validation error', details=None):
        super().__init__('VALIDATION_ERROR', message, details, 400)


class ConflictError(AppError):
    def __init__(self, message='Resource conflict'):
        super().__init__('CONFLICT', message, status_code=409)


class PaymentRequiredError(AppError):
    def __init__(self, message='Enrollment or payment required'):
        super().__init__('PAYMENT_REQUIRED', message, status_code=402)


class ForbiddenError(AppError):
    def __init__(self, message='Insufficient permissions'):
        super().__init__('FORBIDDEN', message, status_code=403)


class NotFoundError(AppError):
    def __init__(self, message='Resource not found'):
        super().__init__('NOT_FOUND', message, status_code=404)


def custom_exception_handler(exc, context):
    if isinstance(exc, AppError):
        return Response(exc.detail, status=exc.status_code)

    response = exception_handler(exc, context)

    if response is not None:
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            response.data = {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Missing or invalid authentication token.',
                }
            }
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            response.data = {
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'Insufficient permissions.',
                }
            }
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            response.data = {
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Resource not found.',
                }
            }
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            response.data = {
                'error': {
                    'code': 'RATE_LIMITED',
                    'message': 'Too many requests. Please try again later.',
                }
            }
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            response.data = {
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Method not allowed.',
                }
            }
        elif response.status_code >= 400 and not isinstance(response.data, dict):
            # DRF validation errors come as dicts of field->messages
            if isinstance(response.data, dict) and 'error' not in response.data:
                details = []
                for field, messages in response.data.items():
                    if isinstance(messages, list):
                        for msg in messages:
                            details.append({'field': field, 'message': str(msg)})
                    else:
                        details.append({'field': field, 'message': str(messages)})
                response.data = {
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Request validation failed.',
                        'details': details,
                    }
                }

    return response
