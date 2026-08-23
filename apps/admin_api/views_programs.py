from rest_framework import viewsets

from apps.core.permissions import IsAdminOrAssistant, IsAdminOrAssistantNoCreateDelete
from apps.programs.models import (
    Program, Degree, Step, Asset, QCMQuestion, FormFieldDef,
    DegreeFile, PriseDeContact, PriseDeContactAsset,
)
from .serializers import (
    AdminProgramSerializer, AdminProgramDetailSerializer,
    AdminDegreeSerializer, AdminDegreeDetailSerializer,
    AdminStepSerializer, AdminStepDetailSerializer,
    AdminAssetSerializer, AdminQCMQuestionSerializer, AdminFormFieldSerializer,
    AdminDegreeFileSerializer, AdminPriseDeContactSerializer, AdminPdcAssetSerializer,
)


class AdminProgramViewSet(viewsets.ModelViewSet):
    serializer_class = AdminProgramSerializer
    permission_classes = [IsAdminOrAssistantNoCreateDelete]
    queryset = Program.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminProgramDetailSerializer
        return AdminProgramSerializer


class AdminDegreeViewSet(viewsets.ModelViewSet):
    serializer_class = AdminDegreeSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminDegreeDetailSerializer
        return AdminDegreeSerializer

    def get_queryset(self):
        qs = Degree.objects.all().order_by('order_index')
        program_id = self.request.query_params.get('programId')
        if program_id:
            qs = qs.filter(program_id=program_id)
        return qs

    def perform_destroy(self, instance):
        from apps.progress.models import StepProgress, AssetCompletion, QCMAttempt, FormSubmission
        steps = instance.steps.all()
        assets = Asset.objects.filter(step__in=steps)
        StepProgress.objects.filter(step__in=steps).delete()
        AssetCompletion.objects.filter(asset__in=assets).delete()
        QCMAttempt.objects.filter(asset__in=assets).delete()
        FormSubmission.objects.filter(asset__in=assets).delete()
        instance.delete()


class AdminStepViewSet(viewsets.ModelViewSet):
    serializer_class = AdminStepSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminStepDetailSerializer
        return AdminStepSerializer

    def get_queryset(self):
        qs = Step.objects.all().order_by('order_index')
        degree_id = self.request.query_params.get('degreeId')
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        return qs

    def perform_destroy(self, instance):
        from apps.progress.models import StepProgress, AssetCompletion, QCMAttempt, FormSubmission
        assets = instance.assets.all()
        StepProgress.objects.filter(step=instance).delete()
        AssetCompletion.objects.filter(asset__in=assets).delete()
        QCMAttempt.objects.filter(asset__in=assets).delete()
        FormSubmission.objects.filter(asset__in=assets).delete()
        instance.delete()


class AdminAssetViewSet(viewsets.ModelViewSet):
    serializer_class = AdminAssetSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = Asset.objects.all().order_by('order_index')
        step_id = self.request.query_params.get('stepId')
        program_id = self.request.query_params.get('programId')
        if step_id:
            qs = qs.filter(step_id=step_id)
        elif program_id:
            # Return standalone form assets belonging to this program (no step)
            qs = qs.filter(program_id=program_id, step__isnull=True)
        return qs

    def _program_kwargs(self):
        pid, sid = self.request.data.get('programId'), self.request.data.get('stepId')
        return {'program_id': pid} if (pid and not sid) else {}

    def perform_create(self, serializer):
        self._save_nested(serializer.save(**self._program_kwargs()), self.request.data)

    def perform_update(self, serializer):
        self._save_nested(serializer.save(**self._program_kwargs()), self.request.data)

    def _save_nested(self, asset, data):
        """Save nested QCM questions and form fields from request payload."""
        from apps.programs.models import QCMQuestion, FormFieldDef

        questions = data.get('questions')
        if questions is not None and asset.type == 'qcm':
            asset.questions.all().delete()
            for i, q in enumerate(questions):
                QCMQuestion.objects.create(
                    asset=asset,
                    question=q.get('question', ''),
                    options=q.get('options', []),
                    correct_index=q.get('correctIndex', 0),
                    order_index=q.get('index', i),
                )

        form_fields = data.get('formFields')
        if form_fields is not None and asset.type == 'form':
            asset.form_fields.all().delete()
            for i, f in enumerate(form_fields):
                FormFieldDef.objects.create(
                    id=f.get('id', f'field_{asset.id}_{i}'),
                    asset=asset,
                    label=f.get('label', ''),
                    type=f.get('type', 'text'),
                    required=f.get('required', False),
                    select_options=f.get('selectOptions'),
                    order_index=f.get('orderIndex', i),
                )


class AdminQCMQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminQCMQuestionSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = QCMQuestion.objects.all().order_by('order_index')
        asset_id = self.request.query_params.get('assetId')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class AdminFormFieldViewSet(viewsets.ModelViewSet):
    serializer_class = AdminFormFieldSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = FormFieldDef.objects.all().order_by('order_index')
        asset_id = self.request.query_params.get('assetId')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class AdminDegreeFileViewSet(viewsets.ModelViewSet):
    serializer_class = AdminDegreeFileSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = DegreeFile.objects.all().order_by('order_index')
        degree_id = self.request.query_params.get('degreeId')
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        return qs


class AdminPriseDeContactViewSet(viewsets.ModelViewSet):
    serializer_class = AdminPriseDeContactSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = PriseDeContact.objects.all().order_by('order_index')
        program_id = self.request.query_params.get('programId')
        degree_id = self.request.query_params.get('degreeId')
        step_id = self.request.query_params.get('stepId')
        if program_id:
            qs = qs.filter(program_id=program_id)
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        if step_id:
            qs = qs.filter(step_id=step_id)
        return qs


class AdminPdcAssetViewSet(viewsets.ModelViewSet):
    serializer_class = AdminPdcAssetSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = PriseDeContactAsset.objects.all().order_by('order_index')
        pdc_id = self.request.query_params.get('priseDeContactId')
        if pdc_id:
            qs = qs.filter(prise_de_contact_id=pdc_id)
        return qs
