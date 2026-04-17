from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'programs', views.AdminProgramViewSet, basename='admin-program')
router.register(r'degrees', views.AdminDegreeViewSet, basename='admin-degree')
router.register(r'steps', views.AdminStepViewSet, basename='admin-step')
router.register(r'assets', views.AdminAssetViewSet, basename='admin-asset')
router.register(r'qcm-questions', views.AdminQCMQuestionViewSet, basename='admin-qcm-question')
router.register(r'form-fields', views.AdminFormFieldViewSet, basename='admin-form-field')
router.register(r'degree-files', views.AdminDegreeFileViewSet, basename='admin-degree-file')
router.register(r'prise-de-contact', views.AdminPriseDeContactViewSet, basename='admin-pdc')
router.register(r'pdc-assets', views.AdminPdcAssetViewSet, basename='admin-pdc-asset')
router.register(r'sessions', views.AdminSessionViewSet, basename='admin-session')
router.register(r'users', views.AdminUserViewSet, basename='admin-user')
router.register(r'enrollments', views.AdminEnrollmentViewSet, basename='admin-enrollment')
router.register(r'payments', views.AdminPaymentViewSet, basename='admin-payment')
router.register(r'testimonies', views.AdminTestimonyViewSet, basename='admin-testimony')
router.register(r'faqs', views.AdminFAQViewSet, basename='admin-faq')
router.register(r'contact-submissions', views.AdminContactSubmissionViewSet, basename='admin-contact-submission')
router.register(r'promo-codes', views.AdminPromoCodeViewSet, basename='admin-promo-code')
router.register(r'testimony-comments', views.AdminTestimonyCommentViewSet, basename='admin-testimony-comment')

urlpatterns = [
    path('', include(router.urls)),
    path('contact-info/', views.AdminContactInfoView.as_view(), name='admin-contact-info'),
    path('app-settings/', views.AdminAppSettingsView.as_view(), name='admin-app-settings'),
    path('upload/', views.AdminFileUploadView.as_view(), name='admin-upload'),
    path('stats/overview/', views.AdminStatsOverviewView.as_view(), name='admin-stats-overview'),
    path('stats/enrollments/', views.AdminEnrollmentTrendsView.as_view(), name='admin-stats-enrollments'),
    path('stats/revenue/', views.AdminRevenueTrendsView.as_view(), name='admin-stats-revenue'),
    path('stats/completion/', views.AdminCompletionStatsView.as_view(), name='admin-stats-completion'),
    path('users/<str:user_id>/progress/', views.AdminUserProgressView.as_view(), name='admin-user-progress'),
    path('stats/progress/', views.AdminProgressStatsView.as_view(), name='admin-progress-stats'),
    path('stats/progress/export/', views.AdminProgressExportView.as_view(), name='admin-progress-export'),
    path('mandataires/', views.AdminMandataireListView.as_view(), name='admin-mandataires'),
]
