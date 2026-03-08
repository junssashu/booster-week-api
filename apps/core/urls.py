from django.urls import path

from . import views

urlpatterns = [
    path('config/app', views.AppConfigView.as_view(), name='app-config'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]
