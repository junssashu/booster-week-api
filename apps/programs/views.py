import math

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiParameter
from rest_framework import generics
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.core.exceptions import ForbiddenError, NotFoundError, PaymentRequiredError
from apps.core.pagination import CustomPagination

from .models import Asset, Degree, Program, Step, PriseDeContact
from .serializers import (
    AssetDetailSerializer,
    DegreeDetailSerializer,
    DegreeListSerializer,
    PriseDeContactSerializer,
    ProgramDetailSerializer,
    ProgramListSerializer,
    StepDetailSerializer,
    StepListSerializer,
)


# ── Reusable error response schemas ──────────────────────────────────────────

_error_detail_serializer = inline_serializer(
    name='ErrorDetail',
    fields={
        'code': drf_serializers.CharField(),
        'message': drf_serializers.CharField(),
    },
)

_not_found_response = inline_serializer(
    name='NotFoundErrorResponse',
    fields={
        'error': inline_serializer(
            name='NotFoundErrorDetail',
            fields={
                'code': drf_serializers.CharField(default='NOT_FOUND'),
                'message': drf_serializers.CharField(default='Resource not found.'),
            },
        ),
    },
)

_unauthorized_response = inline_serializer(
    name='UnauthorizedErrorResponse',
    fields={
        'error': inline_serializer(
            name='UnauthorizedErrorDetail',
            fields={
                'code': drf_serializers.CharField(default='UNAUTHORIZED'),
                'message': drf_serializers.CharField(default='Missing or invalid authentication token.'),
            },
        ),
    },
)

_payment_required_response = inline_serializer(
    name='PaymentRequiredErrorResponse',
    fields={
        'error': inline_serializer(
            name='PaymentRequiredErrorDetail',
            fields={
                'code': drf_serializers.CharField(default='PAYMENT_REQUIRED'),
                'message': drf_serializers.CharField(default='Enrollment or payment required.'),
            },
        ),
    },
)

_forbidden_response = inline_serializer(
    name='ForbiddenErrorResponse',
    fields={
        'error': inline_serializer(
            name='ForbiddenErrorDetail',
            fields={
                'code': drf_serializers.CharField(default='FORBIDDEN'),
                'message': drf_serializers.CharField(default='Insufficient permissions.'),
            },
        ),
    },
)

_AUTH_ENROLLED_ERRORS = {
    401: _unauthorized_response,
    402: _payment_required_response,
    403: _forbidden_response,
    404: _not_found_response,
}


def _get_enrollment_and_check_access(user, program):
    """Returns enrollment or raises appropriate error."""
    from apps.enrollments.models import Enrollment
    enrollment = Enrollment.objects.filter(user=user, program=program).first()
    if not enrollment:
        raise PaymentRequiredError('You must be enrolled in this program.')
    if enrollment.payment_status == 'pending':
        raise PaymentRequiredError('Payment is required to access this content.')
    return enrollment


def _check_degree_accessible(enrollment, degree):
    """Check if degree is accessible based on payment and completion rules."""
    accessible, lock_reason = enrollment.can_access_degree_detail(degree)
    if not accessible:
        if lock_reason == 'completion':
            raise ForbiddenError('Complete previous degrees with at least 70% average to unlock this degree.')
        raise ForbiddenError('Complete second payment to unlock this degree.')


def _check_step_accessible(user, step):
    """Check step is not locked."""
    from apps.progress.models import StepProgress
    sp = StepProgress.objects.filter(user=user, step=step).first()
    if sp:
        if sp.status == 'locked':
            raise ForbiddenError('Complete previous step first.')
        return  # Has progress record and not locked — accessible
    # No progress record: first step (no previous) is always accessible
    prev_step = step.degree.steps.filter(order_index__lt=step.order_index).order_by('-order_index').first()
    if not prev_step:
        return
    # For other steps, check if previous step is completed (70%+)
    prev_sp = StepProgress.objects.filter(user=user, step=prev_step).first()
    if prev_sp and prev_sp.completion_percentage >= 70:
        return
    raise ForbiddenError('Complete previous step first.')


class ProgramListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Programs'],
        operation_id='program_list',
        summary='List programs',
        description=(
            'Retrieve a paginated list of active programs. Supports filtering '
            'by price range and duration, sorting by price, duration, name, or '
            'creation date, and pagination via `page` and `limit` query parameters.'
        ),
        parameters=[
            OpenApiParameter(
                name='price_min',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Minimum price filter (inclusive).',
            ),
            OpenApiParameter(
                name='price_max',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Maximum price filter (inclusive).',
            ),
            OpenApiParameter(
                name='durationWeeks',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Exact duration in weeks to filter by.',
            ),
            OpenApiParameter(
                name='sort',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Field to sort results by. Defaults to `created_at`.',
                enum=['price', 'durationWeeks', 'name', 'created_at'],
            ),
            OpenApiParameter(
                name='order',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Sort direction. `asc` for ascending (default), `desc` for descending.',
                enum=['asc', 'desc'],
            ),
            OpenApiParameter(
                name='page',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Page number (default: 1).',
            ),
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Number of items per page (default: 20, max: 100).',
            ),
        ],
        responses={
            200: inline_serializer(
                name='PaginatedProgramListResponse',
                fields={
                    'data': ProgramListSerializer(many=True),
                    'pagination': inline_serializer(
                        name='ProgramPaginationMeta',
                        fields={
                            'page': drf_serializers.IntegerField(),
                            'limit': drf_serializers.IntegerField(),
                            'totalItems': drf_serializers.IntegerField(),
                            'totalPages': drf_serializers.IntegerField(),
                            'hasNext': drf_serializers.BooleanField(),
                            'hasPrev': drf_serializers.BooleanField(),
                        },
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='ProgramListExample',
                summary='A page of programs',
                value={
                    'data': [
                        {
                            'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                            'name': 'Booster Week Intensive',
                            'description': 'An 8-week intensive program covering core business skills.',
                            'imageUrl': 'https://cdn.example.com/programs/booster-week.jpg',
                            'price': 150000,
                            'durationWeeks': 8,
                            'presentationVideoUrl': 'https://cdn.example.com/videos/intro.mp4',
                            'degreeCount': 3,
                            'createdAt': '2025-09-15T10:30:00Z',
                        },
                    ],
                    'pagination': {
                        'page': 1,
                        'limit': 20,
                        'totalItems': 1,
                        'totalPages': 1,
                        'hasNext': False,
                        'hasPrev': False,
                    },
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
    )
    def get(self, request):
        qs = Program.objects.filter(is_active=True)

        # Filtering
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')
        duration = request.query_params.get('durationWeeks')

        if price_min:
            qs = qs.filter(price__gte=int(price_min))
        if price_max:
            qs = qs.filter(price__lte=int(price_max))
        if duration:
            qs = qs.filter(duration_weeks=int(duration))

        # Sorting
        sort_field = request.query_params.get('sort', 'created_at')
        order = request.query_params.get('order', 'asc')
        sort_map = {
            'price': 'price',
            'durationWeeks': 'duration_weeks',
            'name': 'name',
            'created_at': 'created_at',
        }
        db_field = sort_map.get(sort_field, 'created_at')
        if order == 'desc':
            db_field = f'-{db_field}'
        qs = qs.order_by(db_field)

        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = ProgramListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProgramDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Programs'],
        operation_id='program_detail',
        summary='Get program details',
        description=(
            'Retrieve the full details of a single program, including its '
            'nested list of degrees with step counts.'
        ),
        parameters=[
            OpenApiParameter(
                name='program_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the program.',
            ),
        ],
        responses={
            200: ProgramDetailSerializer,
            404: _not_found_response,
        },
    )
    def get(self, request, program_id):
        try:
            program = Program.objects.prefetch_related('degrees__steps').get(
                id=program_id, is_active=True
            )
        except Program.DoesNotExist:
            raise NotFoundError('Program does not exist.')

        serializer = ProgramDetailSerializer(program)
        return Response(serializer.data)


class ProgramDegreesView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Programs'],
        operation_id='program_degrees_list',
        summary='List degrees of a program',
        description=(
            'Retrieve all degrees belonging to a program, ordered by their '
            'position index. Returns a `data` array wrapper.'
        ),
        parameters=[
            OpenApiParameter(
                name='program_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the parent program.',
            ),
        ],
        responses={
            200: inline_serializer(
                name='DegreeListWrapper',
                fields={
                    'data': DegreeListSerializer(many=True),
                },
            ),
            404: _not_found_response,
        },
    )
    def get(self, request, program_id):
        try:
            program = Program.objects.get(id=program_id, is_active=True)
        except Program.DoesNotExist:
            raise NotFoundError('Program does not exist.')

        degrees = program.degrees.all().order_by('order_index')
        serializer = DegreeListSerializer(degrees, many=True)
        return Response({'data': serializer.data})


class DegreeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Programs'],
        operation_id='degree_detail',
        summary='Get degree details',
        description=(
            'Retrieve the full details of a single degree, including its nested '
            'steps with progress status. Requires authentication and an active '
            'enrollment in the parent program. Access to later degrees may require '
            'a second payment instalment.'
        ),
        parameters=[
            OpenApiParameter(
                name='degree_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the degree.',
            ),
        ],
        responses={
            200: DegreeDetailSerializer,
            **_AUTH_ENROLLED_ERRORS,
        },
    )
    def get(self, request, degree_id):
        try:
            degree = Degree.objects.select_related('program').prefetch_related('steps__assets', 'files').get(id=degree_id)
        except Degree.DoesNotExist:
            raise NotFoundError('Degree does not exist.')

        enrollment = _get_enrollment_and_check_access(request.user, degree.program)
        accessible, lock_reason = enrollment.can_access_degree_detail(degree)

        if not accessible:
            if lock_reason == 'completion':
                raise ForbiddenError('Complete previous degrees with at least 70% average to unlock this degree.')
            raise ForbiddenError('Complete second payment to unlock this degree.')

        ctx = {'user': request.user, 'is_accessible': accessible}
        serializer = DegreeDetailSerializer(degree, context=ctx)
        return Response(serializer.data)


class DegreeStepsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Programs'],
        operation_id='degree_steps_list',
        summary='List steps of a degree',
        description=(
            'Retrieve all steps belonging to a degree, ordered by position index. '
            'Each step includes its current progress status, asset count, and '
            'consigne acceptance state for the authenticated user. Requires '
            'enrollment and degree access.'
        ),
        parameters=[
            OpenApiParameter(
                name='degree_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the parent degree.',
            ),
        ],
        responses={
            200: inline_serializer(
                name='StepListWrapper',
                fields={
                    'data': StepListSerializer(many=True),
                },
            ),
            **_AUTH_ENROLLED_ERRORS,
        },
    )
    def get(self, request, degree_id):
        try:
            degree = Degree.objects.select_related('program').get(id=degree_id)
        except Degree.DoesNotExist:
            raise NotFoundError('Degree does not exist.')

        enrollment = _get_enrollment_and_check_access(request.user, degree.program)
        _check_degree_accessible(enrollment, degree)

        steps = degree.steps.all().order_by('order_index')
        ctx = {'user': request.user}
        serializer = StepListSerializer(steps, many=True, context=ctx)
        return Response({'data': serializer.data})


class StepDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Programs'],
        operation_id='step_detail',
        summary='Get step details',
        description=(
            'Retrieve the full details of a single step, including its nested '
            'assets. If the step contains a consigne asset that has not been '
            'accepted yet, only the consigne asset is returned in the assets '
            'list. Requires authentication, enrollment, degree access, and '
            'sequential step completion.'
        ),
        parameters=[
            OpenApiParameter(
                name='step_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the step.',
            ),
        ],
        responses={
            200: StepDetailSerializer,
            **_AUTH_ENROLLED_ERRORS,
        },
    )
    def get(self, request, step_id):
        try:
            step = Step.objects.select_related('degree__program').prefetch_related('assets').get(id=step_id)
        except Step.DoesNotExist:
            raise NotFoundError('Step does not exist.')

        enrollment = _get_enrollment_and_check_access(request.user, step.degree.program)
        _check_degree_accessible(enrollment, step.degree)
        _check_step_accessible(request.user, step)

        ctx = {'user': request.user}
        serializer = StepDetailSerializer(step, context=ctx)
        return Response(serializer.data)


class AssetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Programs'],
        operation_id='asset_detail',
        summary='Get asset details',
        description=(
            'Retrieve the full details of a single asset. The response shape '
            'depends on the asset type:\n\n'
            '- **video / pdf / text / link**: core fields plus `isCompleted`.\n'
            '- **consigne**: includes `consigneText` and `isAccepted`.\n'
            '- **qcm**: includes `passingScore`, `lastScore`, and `questions` array.\n'
            '- **form**: includes `formFields` array with field definitions.\n\n'
            'Requires authentication, enrollment, degree access, sequential step '
            'completion, and consigne acceptance when the parent step has one.'
        ),
        parameters=[
            OpenApiParameter(
                name='asset_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the asset.',
            ),
        ],
        responses={
            200: AssetDetailSerializer,
            **_AUTH_ENROLLED_ERRORS,
        },
        examples=[
            OpenApiExample(
                name='VideoAssetExample',
                summary='A video asset response',
                value={
                    'id': 'f1a2b3c4-d5e6-7890-abcd-ef1234567890',
                    'type': 'video',
                    'title': 'Introduction to Marketing',
                    'description': 'An overview of fundamental marketing concepts.',
                    'externalUrl': 'https://cdn.example.com/videos/marketing-intro.mp4',
                    'orderIndex': 1,
                    'isCompleted': False,
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                name='QCMAssetExample',
                summary='A QCM quiz asset response',
                value={
                    'id': 'a9b8c7d6-e5f4-3210-fedc-ba0987654321',
                    'type': 'qcm',
                    'title': 'Marketing Fundamentals Quiz',
                    'description': 'Test your understanding of core concepts.',
                    'externalUrl': None,
                    'orderIndex': 3,
                    'isCompleted': True,
                    'passingScore': 70,
                    'lastScore': 85.0,
                    'questions': [
                        {
                            'index': 0,
                            'question': 'What is the primary goal of branding?',
                            'options': [
                                'Increase costs',
                                'Build recognition and trust',
                                'Reduce product quality',
                                'Limit market reach',
                            ],
                        },
                    ],
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                name='ConsigneAssetExample',
                summary='A consigne asset response',
                value={
                    'id': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
                    'type': 'consigne',
                    'title': 'Module Guidelines',
                    'description': 'Read and accept before proceeding.',
                    'externalUrl': None,
                    'orderIndex': 0,
                    'consigneText': 'You must complete all exercises independently.',
                    'isAccepted': False,
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
    )
    def get(self, request, asset_id):
        try:
            asset = Asset.objects.select_related('step__degree__program').get(id=asset_id)
        except Asset.DoesNotExist:
            raise NotFoundError('Asset does not exist.')

        step = asset.step
        enrollment = _get_enrollment_and_check_access(request.user, step.degree.program)
        _check_degree_accessible(enrollment, step.degree)
        _check_step_accessible(request.user, step)

        # Consigne gate for non-consigne assets
        if asset.type != 'consigne':
            has_consigne = step.assets.filter(type='consigne').exists()
            if has_consigne:
                from apps.progress.models import ConsigneAcceptance
                if not ConsigneAcceptance.objects.filter(user=request.user, step=step).exists():
                    raise ForbiddenError('Accept the consigne before accessing this content.')

        ctx = {'user': request.user}
        serializer = AssetDetailSerializer(asset, context=ctx)
        return Response(serializer.data)


class ProgramPriseDeContactView(generics.RetrieveAPIView):
    serializer_class = PriseDeContactSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        program_id = self.kwargs['program_id']
        return get_object_or_404(PriseDeContact, program_id=program_id)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user'] = self.request.user
        return ctx


class DegreePriseDeContactView(generics.RetrieveAPIView):
    serializer_class = PriseDeContactSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        degree_id = self.kwargs['degree_id']
        return get_object_or_404(PriseDeContact, degree_id=degree_id)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user'] = self.request.user
        return ctx


class StepPriseDeContactView(generics.RetrieveAPIView):
    serializer_class = PriseDeContactSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        step_id = self.kwargs['step_id']
        return get_object_or_404(PriseDeContact, step_id=step_id)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user'] = self.request.user
        return ctx
