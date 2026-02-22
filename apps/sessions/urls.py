from django.urls import path

from . import views

urlpatterns = [
    path('sessions', views.SessionListView.as_view(), name='session-list'),
    path('sessions/<str:session_id>', views.SessionDetailView.as_view(), name='session-detail'),
]
