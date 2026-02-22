from django.urls import path

from . import views

urlpatterns = [
    path('testimonies', views.TestimonyListCreateView.as_view(), name='testimony-list-create'),
    path('testimonies/<str:testimony_id>', views.TestimonyDeleteView.as_view(), name='testimony-delete'),
    path('testimonies/<str:testimony_id>/like', views.TestimonyLikeView.as_view(), name='testimony-like'),
    path('testimonies/<str:testimony_id>/heart', views.TestimonyHeartView.as_view(), name='testimony-heart'),
    path('testimonies/<str:testimony_id>/comments', views.CommentListCreateView.as_view(), name='comment-list-create'),
    path('testimonies/<str:testimony_id>/comments/<str:comment_id>', views.CommentDeleteView.as_view(), name='comment-delete'),
]
