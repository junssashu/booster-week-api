from django.urls import path

from . import views
from .views_enrollment_form import ProgramEnrollmentFormView, ProgramEnrollmentFormSubmitView

urlpatterns = [
    path('programs', views.ProgramListView.as_view(), name='program-list'),
    path('programs/<str:program_id>', views.ProgramDetailView.as_view(), name='program-detail'),
    path('programs/<str:program_id>/degrees', views.ProgramDegreesView.as_view(), name='program-degrees'),
    path('degrees/<str:degree_id>', views.DegreeDetailView.as_view(), name='degree-detail'),
    path('degrees/<str:degree_id>/steps', views.DegreeStepsView.as_view(), name='degree-steps'),
    path('steps/<str:step_id>', views.StepDetailView.as_view(), name='step-detail'),
    path('assets/<str:asset_id>', views.AssetDetailView.as_view(), name='asset-detail'),
    path('programs/<str:program_id>/prise-de-contact', views.ProgramPriseDeContactView.as_view(), name='program-pdc'),
    path('degrees/<str:degree_id>/prise-de-contact', views.DegreePriseDeContactView.as_view(), name='degree-pdc'),
    path('steps/<str:step_id>/prise-de-contact', views.StepPriseDeContactView.as_view(), name='step-pdc'),
    path('programs/<str:program_id>/enrollment-form', ProgramEnrollmentFormView.as_view(), name='program-enrollment-form'),
    path('programs/<str:program_id>/enrollment-form/submit', ProgramEnrollmentFormSubmitView.as_view(), name='program-enrollment-form-submit'),
]
