from django.urls import path

from . import views

urlpatterns = [
    path('programs', views.ProgramListView.as_view(), name='program-list'),
    path('programs/<str:program_id>', views.ProgramDetailView.as_view(), name='program-detail'),
    path('programs/<str:program_id>/degrees', views.ProgramDegreesView.as_view(), name='program-degrees'),
    path('degrees/<str:degree_id>', views.DegreeDetailView.as_view(), name='degree-detail'),
    path('degrees/<str:degree_id>/steps', views.DegreeStepsView.as_view(), name='degree-steps'),
    path('steps/<str:step_id>', views.StepDetailView.as_view(), name='step-detail'),
    path('assets/<str:asset_id>', views.AssetDetailView.as_view(), name='asset-detail'),
]
