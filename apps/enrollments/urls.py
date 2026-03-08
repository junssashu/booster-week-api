from django.urls import path

from . import views

urlpatterns = [
    path('enrollments', views.EnrollmentListCreateView.as_view(), name='enrollment-list-create'),
    path('enrollments/<str:enrollment_id>', views.EnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('enrollments/<str:enrollment_id>/payments', views.EnrollmentPaymentsView.as_view(), name='enrollment-payments'),
    path('payments/initiate', views.PaymentInitiateView.as_view(), name='payment-initiate'),
    path('payments/webhook', views.PaymentWebhookView.as_view(), name='payment-webhook'),
    path('payments/<str:payment_id>/status', views.PaymentStatusView.as_view(), name='payment-status'),
    path('payments/<str:payment_id>/dev-simulate', views.DevPaymentSimulateView.as_view(), name='payment-dev-simulate'),
    path('promo-codes/generate', views.PromoCodeGenerateView.as_view(), name='promo-code-generate'),
    path('promo-codes/validate', views.PromoCodeValidateView.as_view(), name='promo-code-validate'),
    path('promo-codes', views.PromoCodeListView.as_view(), name='promo-code-list'),
]
