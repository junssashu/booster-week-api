from django.urls import path

from . import views

urlpatterns = [
    path('progress', views.ProgressView.as_view(), name='progress'),
    path('progress/assets/<str:asset_id>/complete', views.MarkAssetCompleteView.as_view(), name='mark-asset-complete'),
    path('assets/<str:asset_id>/qcm/submit', views.QCMSubmitView.as_view(), name='qcm-submit'),
    path('assets/<str:asset_id>/form/submit', views.FormSubmitView.as_view(), name='form-submit'),
    path('steps/<str:step_id>/consigne/accept', views.ConsigneAcceptView.as_view(), name='consigne-accept'),
]
