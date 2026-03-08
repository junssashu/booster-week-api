from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    path('', include('apps.core.urls')),
    path('', include('apps.accounts.urls')),
    path('', include('apps.programs.urls')),
    path('', include('apps.enrollments.urls')),
    path('', include('apps.progress.urls')),
    path('', include('apps.sessions.urls')),
    path('', include('apps.testimonies.urls')),
    path('', include('apps.content.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),
    path('api/v1/admin/', include('apps.admin_api.urls')),
    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
