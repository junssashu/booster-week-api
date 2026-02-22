from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiParameter
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import NotFoundError
from apps.core.pagination import CustomPagination

from .models import LiveReplaySession
from .serializers import SessionSerializer


class SessionListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Sessions'],
        operation_id='session_list',
        summary='List sessions',
        description=(
            'Retrieve a paginated list of live and replay sessions. '
            'Supports filtering by live status, sorting by date, and '
            'pagination via `page` and `limit` query parameters.'
        ),
        parameters=[
            OpenApiParameter(
                name='isLive',
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by live status. Pass `true` for live sessions or `false` for replays.',
            ),
            OpenApiParameter(
                name='sort',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Field to sort by. Currently supported: `date` (default).',
                enum=['date'],
            ),
            OpenApiParameter(
                name='order',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Sort direction. `asc` for ascending, `desc` for descending (default).',
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
                name='PaginatedSessionListResponse',
                fields={
                    'data': SessionSerializer(many=True),
                    'pagination': inline_serializer(
                        name='SessionPaginationMeta',
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
    )
    def get(self, request):
        qs = LiveReplaySession.objects.all()

        is_live = request.query_params.get('isLive')
        if is_live is not None:
            qs = qs.filter(is_live=is_live.lower() == 'true')

        sort = request.query_params.get('sort', 'date')
        order = request.query_params.get('order', 'desc')
        sort_map = {'date': 'date'}
        db_field = sort_map.get(sort, 'date')
        if order == 'desc':
            db_field = f'-{db_field}'
        qs = qs.order_by(db_field)

        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = SessionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SessionDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Sessions'],
        operation_id='session_detail',
        summary='Get session details',
        description=(
            'Retrieve the full details of a single live or replay session by its ID.'
        ),
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the session to retrieve.',
            ),
        ],
        responses={
            200: SessionSerializer,
            404: inline_serializer(
                name='SessionNotFoundResponse',
                fields={
                    'error': inline_serializer(
                        name='SessionNotFoundError',
                        fields={
                            'code': drf_serializers.CharField(default='NOT_FOUND'),
                            'message': drf_serializers.CharField(default='Session does not exist.'),
                        },
                    ),
                },
            ),
        },
    )
    def get(self, request, session_id):
        try:
            session = LiveReplaySession.objects.get(id=session_id)
        except LiveReplaySession.DoesNotExist:
            raise NotFoundError('Session does not exist.')

        serializer = SessionSerializer(session)
        return Response(serializer.data)
