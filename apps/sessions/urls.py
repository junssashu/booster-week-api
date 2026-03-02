from django.urls import path

from . import views

urlpatterns = [
    path('sessions', views.SessionListView.as_view(), name='session-list'),
    path('sessions/<str:session_id>', views.SessionDetailView.as_view(), name='session-detail'),
    path('sessions/<str:session_id>/join', views.JoinSessionView.as_view(), name='session-join'),
]
