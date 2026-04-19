from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as drf_serializers

from .serializers import (
    EnrollmentListSerializer,
    PaymentSerializer,
    PaymentInitiateSerializer,
    PaymentHistorySerializer,
    PaymentStatusSerializer,
)

_ErrorDetailSchema = inline_serializer(
    name='ErrorDetail',
    fields={
        'field': drf_serializers.CharField(),
        'message': drf_serializers.CharField(),
    },
)

_ErrorResponseSchema = inline_serializer(
    name='ErrorResponse',
    fields={
        'error': inline_serializer(
            name='ErrorBody',
            fields={
                'code': drf_serializers.CharField(),
                'message': drf_serializers.CharField(),
                'details': drf_serializers.ListField(
                    child=_ErrorDetailSchema, required=False,
                ),
            },
        ),
    },
)

_EnrollmentListResponseSchema = inline_serializer(
    name='EnrollmentListResponse',
    fields={
        'data': EnrollmentListSerializer(many=True),
    },
)

_EnrollmentCreateResponseSchema = inline_serializer(
    name='EnrollmentCreateResponse',
    fields={
        'data': inline_serializer(
            name='EnrollmentCreateData',
            fields={
                'id': drf_serializers.CharField(),
                'programId': drf_serializers.CharField(),
                'userId': drf_serializers.CharField(),
                'paymentType': drf_serializers.ChoiceField(choices=['full', 'installment']),
                'paymentStatus': drf_serializers.CharField(),
                'amountPaid': drf_serializers.IntegerField(),
                'totalAmount': drf_serializers.IntegerField(),
                'installmentAmount': drf_serializers.IntegerField(allow_null=True),
                'enrollmentDate': drf_serializers.DateTimeField(),
                'payments': PaymentSerializer(many=True),
            },
        ),
    },
)

_PaymentInitiateResponseSchema = inline_serializer(
    name='PaymentInitiateResponse',
    fields={
        'data': inline_serializer(
            name='PaymentInitiateData',
            fields={
                'paymentId': drf_serializers.CharField(),
                'transactionId': drf_serializers.CharField(),
                'status': drf_serializers.CharField(),
                'message': drf_serializers.CharField(),
                'expiresAt': drf_serializers.DateTimeField(),
                'paymentUrl': drf_serializers.URLField(required=False),
            },
        ),
    },
)

_PaymentListResponseSchema = inline_serializer(
    name='PaymentListResponse',
    fields={
        'data': PaymentSerializer(many=True),
    },
)

_WebhookReceivedSchema = inline_serializer(
    name='WebhookReceived',
    fields={
        'received': drf_serializers.BooleanField(),
    },
)

_DevSimulateResponseSchema = inline_serializer(
    name='DevSimulateResponse',
    fields={
        'data': inline_serializer(
            name='DevSimulateData',
            fields={
                'paymentId': drf_serializers.CharField(),
                'status': drf_serializers.CharField(),
                'enrollmentPaymentStatus': drf_serializers.CharField(),
                'amountPaid': drf_serializers.IntegerField(),
                'message': drf_serializers.CharField(),
            },
        ),
    },
)

_DevSimulateRequestSchema = inline_serializer(
    name='DevSimulateRequest',
    fields={
        'status': drf_serializers.ChoiceField(
            choices=['completed', 'failed'],
            required=False,
            help_text='Desired payment outcome. Defaults to "completed".',
        ),
    },
)

_GatewayErrorSchema = inline_serializer(
    name='GatewayErrorResponse',
    fields={
        'error': inline_serializer(
            name='GatewayErrorBody',
            fields={
                'code': drf_serializers.CharField(),
                'message': drf_serializers.CharField(),
            },
        ),
    },
)

_MONTHS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
