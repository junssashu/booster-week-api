from django.db.models import F
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from apps.core.pagination import CustomPagination
from apps.core.throttles import TestimonyThrottle

from .models import Testimony, TestimonyComment, TestimonyReaction
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    TestimonyCreateSerializer,
    TestimonySerializer,
)


class TestimonyListCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Testimonies'],
        operation_id='testimonies_list',
        summary='List testimonies (paginated)',
        description=(
            'Returns a paginated list of testimonies. Supports sorting by createdAt '
            'or likeCount in ascending or descending order. '
            'Authenticated users receive userHasLiked flag.'
        ),
        parameters=[
            inline_serializer(
                name='TestimonyListQueryParams',
                fields={
                    'sort': drf_serializers.ChoiceField(
                        choices=['createdAt', 'likeCount'],
                        required=False,
                        default='createdAt',
                        help_text='Field to sort by.',
                    ),
                    'order': drf_serializers.ChoiceField(
                        choices=['asc', 'desc'],
                        required=False,
                        default='desc',
                        help_text='Sort order.',
                    ),
                    'page': drf_serializers.IntegerField(required=False, default=1, help_text='Page number.'),
                    'limit': drf_serializers.IntegerField(required=False, default=20, help_text='Items per page (max 100).'),
                },
            ),
        ],
        responses={
            200: inline_serializer(
                name='TestimonyListResponse',
                fields={
                    'data': TestimonySerializer(many=True),
                    'pagination': inline_serializer(
                        name='TestimonyPagination',
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
        qs = Testimony.objects.select_related('author').all()

        sort = request.query_params.get('sort', 'createdAt')
        order = request.query_params.get('order', 'desc')
        sort_map = {
            'createdAt': 'created_at',
            'likeCount': 'like_count',
        }
        db_field = sort_map.get(sort, 'created_at')
        if order == 'desc':
            db_field = f'-{db_field}'
        qs = qs.order_by(db_field)

        user = request.user if request.user.is_authenticated else None

        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = TestimonySerializer(page, many=True, context={'user': user})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=['Testimonies'],
        operation_id='testimonies_create',
        summary='Create a testimony',
        description=(
            'Creates a new testimony authored by the authenticated user. '
            'At least one of content (text) or videoUrl must be provided.'
        ),
        request=TestimonyCreateSerializer,
        responses={
            201: inline_serializer(
                name='TestimonyCreateResponse',
                fields={
                    'data': TestimonySerializer(),
                },
            ),
        },
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required.'}},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = TestimonyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Validation failed.', details)

        content = serializer.validated_data.get('content', '')
        video_url = serializer.validated_data.get('videoUrl', '') or serializer.validated_data.get('video_url', '')
        testimony = Testimony.objects.create(
            author=request.user,
            content=content,
            video_url=video_url,
        )

        data = TestimonySerializer(testimony, context={'user': request.user}).data
        return Response({'data': data}, status=status.HTTP_201_CREATED)

    def get_throttles(self):
        if self.request.method == 'POST':
            return [TestimonyThrottle()]
        return []


class TestimonyDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Testimonies'],
        operation_id='testimonies_delete',
        summary='Delete own testimony',
        description='Deletes a testimony. Only the author can delete their own testimony.',
        request=None,
        responses={204: None},
    )
    def delete(self, request, testimony_id):
        try:
            testimony = Testimony.objects.get(id=testimony_id)
        except Testimony.DoesNotExist:
            raise NotFoundError('Testimony does not exist.')

        if testimony.author_id != request.user.id:
            raise ForbiddenError('Testimony authored by another user.')

        testimony.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TestimonyLikeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Testimonies'],
        operation_id='testimonies_like_toggle',
        summary='Toggle like on a testimony',
        description='Toggles the like reaction on a testimony for the authenticated user. Liking again removes the like.',
        request=None,
        responses={
            200: inline_serializer(
                name='TestimonyLikeResponse',
                fields={
                    'data': inline_serializer(
                        name='TestimonyLikeData',
                        fields={
                            'testimonyId': drf_serializers.CharField(),
                            'liked': drf_serializers.BooleanField(help_text='Whether the user now likes this testimony.'),
                            'likeCount': drf_serializers.IntegerField(help_text='Updated total like count.'),
                        },
                    ),
                },
            ),
        },
    )
    def post(self, request, testimony_id):
        try:
            testimony = Testimony.objects.get(id=testimony_id)
        except Testimony.DoesNotExist:
            raise NotFoundError('Testimony does not exist.')

        reaction = TestimonyReaction.objects.filter(
            testimony=testimony, user=request.user, reaction_type='like'
        ).first()

        if reaction:
            reaction.delete()
            Testimony.objects.filter(id=testimony_id).update(like_count=F('like_count') - 1)
            testimony.refresh_from_db()
            liked = False
        else:
            TestimonyReaction.objects.create(
                testimony=testimony, user=request.user, reaction_type='like'
            )
            Testimony.objects.filter(id=testimony_id).update(like_count=F('like_count') + 1)
            testimony.refresh_from_db()
            liked = True

        return Response({
            'data': {
                'testimonyId': testimony.id,
                'liked': liked,
                'likeCount': testimony.like_count,
            }
        })


class CommentListCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Testimonies'],
        operation_id='testimony_comments_list',
        summary='List comments on a testimony',
        description='Returns a paginated list of comments for a specific testimony, ordered by creation date ascending.',
        parameters=[
            inline_serializer(
                name='CommentListQueryParams',
                fields={
                    'page': drf_serializers.IntegerField(required=False, default=1, help_text='Page number.'),
                    'limit': drf_serializers.IntegerField(required=False, default=20, help_text='Items per page (max 100).'),
                },
            ),
        ],
        responses={
            200: inline_serializer(
                name='CommentListResponse',
                fields={
                    'data': CommentSerializer(many=True),
                    'pagination': inline_serializer(
                        name='CommentPagination',
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
    def get(self, request, testimony_id):
        try:
            Testimony.objects.get(id=testimony_id)
        except Testimony.DoesNotExist:
            raise NotFoundError('Testimony does not exist.')

        qs = TestimonyComment.objects.filter(
            testimony_id=testimony_id
        ).select_related('author').order_by('created_at')

        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = CommentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=['Testimonies'],
        operation_id='testimony_comments_create',
        summary='Add a comment to a testimony',
        description='Creates a new comment on a testimony. Content must be between 1 and 2000 characters.',
        request=CommentCreateSerializer,
        responses={
            201: inline_serializer(
                name='CommentCreateResponse',
                fields={
                    'data': CommentSerializer(),
                },
            ),
        },
    )
    def post(self, request, testimony_id):
        if not request.user.is_authenticated:
            return Response(
                {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required.'}},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            testimony = Testimony.objects.get(id=testimony_id)
        except Testimony.DoesNotExist:
            raise NotFoundError('Testimony does not exist.')

        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Validation failed.', details)

        comment = TestimonyComment.objects.create(
            testimony=testimony,
            author=request.user,
            content=serializer.validated_data['content'],
        )

        # Update comment count
        Testimony.objects.filter(id=testimony_id).update(comment_count=F('comment_count') + 1)

        data = CommentSerializer(comment).data
        return Response({'data': data}, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Testimonies'],
        operation_id='testimony_comments_delete',
        summary='Delete own comment',
        description='Deletes a comment from a testimony. Only the comment author can delete it.',
        request=None,
        responses={204: None},
    )
    def delete(self, request, testimony_id, comment_id):
        try:
            comment = TestimonyComment.objects.get(id=comment_id, testimony_id=testimony_id)
        except TestimonyComment.DoesNotExist:
            raise NotFoundError('Comment does not exist.')

        if comment.author_id != request.user.id:
            raise ForbiddenError('Comment authored by another user.')

        comment.delete()
        Testimony.objects.filter(id=testimony_id).update(comment_count=F('comment_count') - 1)
        return Response(status=status.HTTP_204_NO_CONTENT)
