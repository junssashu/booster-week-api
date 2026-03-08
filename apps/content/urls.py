from django.urls import path

from . import views

urlpatterns = [
    path('faq', views.FAQView.as_view(), name='faq'),
    path('contact', views.ContactView.as_view(), name='contact'),
    path('contact/submit', views.ContactSubmitView.as_view(), name='contact-submit'),
]
