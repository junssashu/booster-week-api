from rest_framework import serializers

from .models import Asset, Degree, DegreeFile, FormFieldDef, Program, QCMQuestion, Step, PriseDeContact, PriseDeContactAsset
from apps.core.storage import resolve_url


class PriseDeContactAssetSerializer(serializers.ModelSerializer):
    externalUrl = serializers.SerializerMethodField()
    orderIndex = serializers.IntegerField(source='order_index')

    class Meta:
        model = PriseDeContactAsset
        fields = ['id', 'type', 'title', 'description', 'externalUrl', 'orderIndex']

    def get_externalUrl(self, obj):
        return resolve_url(obj.external_url)


class PriseDeContactSerializer(serializers.ModelSerializer):
    assets = PriseDeContactAssetSerializer(many=True, read_only=True)
    accepted = serializers.SerializerMethodField()
    orderIndex = serializers.IntegerField(source='order_index')

    class Meta:
        model = PriseDeContact
        fields = ['id', 'title', 'description', 'assets', 'accepted', 'orderIndex']

    def get_accepted(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        from apps.progress.models import PriseDeContactAcceptance
        return PriseDeContactAcceptance.objects.filter(
            user=user, prise_de_contact=obj
        ).exists()


class ProgramListSerializer(serializers.ModelSerializer):
    imageUrl = serializers.CharField(source='image_url')
    durationWeeks = serializers.IntegerField(source='duration_weeks')
    presentationVideoUrl = serializers.CharField(source='presentation_video_url', allow_null=True)
    degreeCount = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Program
        fields = ['id', 'name', 'description', 'imageUrl', 'price',
                  'durationWeeks', 'presentationVideoUrl', 'degreeCount', 'createdAt']

    def get_degreeCount(self, obj):
        return obj.degrees.count()


class DegreeListSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id')
    orderIndex = serializers.IntegerField(source='order_index')
    stepCount = serializers.SerializerMethodField()

    class Meta:
        model = Degree
        fields = ['id', 'programId', 'title', 'description', 'orderIndex', 'stepCount']

    def get_stepCount(self, obj):
        return obj.steps.count()


class ProgramDetailSerializer(serializers.ModelSerializer):
    imageUrl = serializers.CharField(source='image_url')
    durationWeeks = serializers.IntegerField(source='duration_weeks')
    presentationVideoUrl = serializers.CharField(source='presentation_video_url', allow_null=True)
    degrees = DegreeListSerializer(many=True, read_only=True)
    createdAt = serializers.DateTimeField(source='created_at')
    priseDeContact = serializers.SerializerMethodField()

    class Meta:
        model = Program
        fields = ['id', 'name', 'description', 'imageUrl', 'price',
                  'durationWeeks', 'presentationVideoUrl', 'degrees', 'createdAt',
                  'priseDeContact']

    def get_priseDeContact(self, obj):
        pdc = obj.prises_de_contact.first()
        if not pdc:
            return None
        return PriseDeContactSerializer(pdc, context=self.context).data


class DegreeFileSerializer(serializers.ModelSerializer):
    orderIndex = serializers.IntegerField(source='order_index')
    externalUrl = serializers.SerializerMethodField()

    class Meta:
        model = DegreeFile
        fields = ['id', 'type', 'title', 'description', 'externalUrl', 'orderIndex']

    def get_externalUrl(self, obj):
        return resolve_url(obj.external_url)


class StepListSerializer(serializers.ModelSerializer):
    degreeId = serializers.CharField(source='degree_id')
    orderIndex = serializers.IntegerField(source='order_index')
    assetCount = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    completionPercentage = serializers.SerializerMethodField()
    hasConsigne = serializers.SerializerMethodField()
    consigneAccepted = serializers.SerializerMethodField()
    videoCount = serializers.SerializerMethodField()
    audioCount = serializers.SerializerMethodField()
    documentCount = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ['id', 'degreeId', 'title', 'description', 'orderIndex',
                  'assetCount', 'status', 'completionPercentage', 'hasConsigne',
                  'consigneAccepted', 'videoCount', 'audioCount', 'documentCount']

    def get_assetCount(self, obj):
        return obj.assets.count()

    def get_videoCount(self, obj):
        return obj.assets.filter(type='video').count()

    def get_audioCount(self, obj):
        return obj.assets.filter(type='audio').count()

    def get_documentCount(self, obj):
        return obj.assets.filter(type='pdf').count()

    def get_status(self, obj):
        user = self.context.get('user')
        if not user:
            return 'locked'
        from apps.progress.models import StepProgress
        sp = StepProgress.objects.filter(user=user, step=obj).first()
        return sp.status if sp else 'locked'

    def get_completionPercentage(self, obj):
        user = self.context.get('user')
        if not user:
            return 0
        from apps.progress.models import StepProgress
        sp = StepProgress.objects.filter(user=user, step=obj).first()
        return sp.completion_percentage if sp else 0

    def get_hasConsigne(self, obj):
        return obj.assets.filter(type='consigne').exists()

    def get_consigneAccepted(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        from apps.progress.models import ConsigneAcceptance
        return ConsigneAcceptance.objects.filter(user=user, step=obj).exists()


class DegreeDetailSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id')
    orderIndex = serializers.IntegerField(source='order_index')
    isAccessible = serializers.SerializerMethodField()
    completionPercentage = serializers.SerializerMethodField()
    presentationVideoUrl = serializers.SerializerMethodField()
    consigne = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    priseDeContact = serializers.SerializerMethodField()

    class Meta:
        model = Degree
        fields = ['id', 'programId', 'title', 'description', 'orderIndex',
                  'isAccessible', 'completionPercentage', 'presentationVideoUrl',
                  'consigne', 'steps', 'files', 'priseDeContact']

    def get_isAccessible(self, obj):
        return self.context.get('is_accessible', True)

    def get_completionPercentage(self, obj):
        """Average of all step completion_percentages for this degree for the current user.
        Steps with no progress count as 0%.
        """
        user = self.context.get('user')
        if not user:
            return 0
        steps = obj.steps.all()
        total_steps = steps.count()
        if total_steps == 0:
            return 0
        from apps.progress.models import StepProgress
        progress_map = dict(
            StepProgress.objects.filter(
                user=user, step__in=steps
            ).values_list('step_id', 'completion_percentage')
        )
        total_pct = sum(progress_map.get(step.id, 0) for step in steps)
        return round(total_pct / total_steps)

    def get_presentationVideoUrl(self, obj):
        """Return the external_url of the first video asset found across steps."""
        for step in obj.steps.all().order_by('order_index'):
            for asset in step.assets.all().order_by('order_index'):
                if asset.type == 'video':
                    return asset.external_url
        return None

    def get_consigne(self, obj):
        """Return the consigne from the first step that has one."""
        for step in obj.steps.all().order_by('order_index'):
            for asset in step.assets.all().order_by('order_index'):
                if asset.type == 'consigne':
                    user = self.context.get('user')
                    accepted = False
                    if user:
                        from apps.progress.models import ConsigneAcceptance
                        accepted = ConsigneAcceptance.objects.filter(
                            user=user, step=step
                        ).exists()
                    return {
                        'stepId': step.id,
                        'assetId': asset.id,
                        'title': asset.title,
                        'consigneText': asset.consigne_text,
                        'accepted': accepted,
                    }
        return None

    def get_steps(self, obj):
        steps = obj.steps.all().order_by('order_index')
        return StepListSerializer(steps, many=True, context=self.context).data

    def get_files(self, obj):
        files = obj.files.all().order_by('order_index')
        return DegreeFileSerializer(files, many=True).data

    def get_priseDeContact(self, obj):
        pdc = obj.prises_de_contact.first()
        if not pdc:
            return None
        return PriseDeContactSerializer(pdc, context=self.context).data


class AssetSummarySerializer(serializers.ModelSerializer):
    """Used when listing assets in step detail."""
    orderIndex = serializers.IntegerField(source='order_index')
    externalUrl = serializers.SerializerMethodField()
    consigneText = serializers.SerializerMethodField()
    passingScore = serializers.SerializerMethodField()
    questionCount = serializers.SerializerMethodField()
    formFields = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ['id', 'type', 'title', 'description', 'externalUrl',
                  'orderIndex', 'consigneText', 'passingScore', 'questionCount', 'formFields']

    def get_externalUrl(self, obj):
        return resolve_url(obj.external_url)

    def get_consigneText(self, obj):
        if obj.type == 'consigne':
            return obj.consigne_text
        return None

    def get_passingScore(self, obj):
        if obj.type == 'qcm':
            return obj.passing_score
        return None

    def get_questionCount(self, obj):
        if obj.type == 'qcm':
            return obj.questions.count()
        return None

    def get_formFields(self, obj):
        if obj.type == 'form':
            return FormFieldSerializer(obj.form_fields.all(), many=True).data
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Remove None fields based on type
        if instance.type != 'consigne':
            data.pop('consigneText', None)
        if instance.type != 'qcm':
            data.pop('passingScore', None)
            data.pop('questionCount', None)
        if instance.type != 'form':
            data.pop('formFields', None)
        return data


class StepDetailSerializer(serializers.ModelSerializer):
    degreeId = serializers.CharField(source='degree_id')
    orderIndex = serializers.IntegerField(source='order_index')
    status = serializers.SerializerMethodField()
    completionPercentage = serializers.SerializerMethodField()
    hasConsigne = serializers.SerializerMethodField()
    consigneAccepted = serializers.SerializerMethodField()
    assets = serializers.SerializerMethodField()
    priseDeContact = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ['id', 'degreeId', 'title', 'description', 'orderIndex',
                  'status', 'completionPercentage', 'hasConsigne',
                  'consigneAccepted', 'assets', 'priseDeContact']

    def get_status(self, obj):
        user = self.context.get('user')
        if not user:
            return 'locked'
        from apps.progress.models import StepProgress
        sp = StepProgress.objects.filter(user=user, step=obj).first()
        return sp.status if sp else 'locked'

    def get_completionPercentage(self, obj):
        user = self.context.get('user')
        if not user:
            return 0
        from apps.progress.models import StepProgress
        sp = StepProgress.objects.filter(user=user, step=obj).first()
        return sp.completion_percentage if sp else 0

    def get_hasConsigne(self, obj):
        return obj.assets.filter(type='consigne').exists()

    def get_consigneAccepted(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        from apps.progress.models import ConsigneAcceptance
        return ConsigneAcceptance.objects.filter(user=user, step=obj).exists()

    def get_assets(self, obj):
        user = self.context.get('user')
        assets = obj.assets.all().order_by('order_index')

        # Consigne gate: if consigne exists and not accepted, only return consigne
        has_consigne = assets.filter(type='consigne').exists()
        if has_consigne and user:
            from apps.progress.models import ConsigneAcceptance
            accepted = ConsigneAcceptance.objects.filter(user=user, step=obj).exists()
            if not accepted:
                assets = assets.filter(type='consigne')

        return AssetSummarySerializer(assets, many=True).data

    def get_priseDeContact(self, obj):
        pdc = obj.prises_de_contact.first()
        if not pdc:
            return None
        return PriseDeContactSerializer(pdc, context=self.context).data


class QCMQuestionSerializer(serializers.ModelSerializer):
    """Serializer for QCM questions — excludes correctIndex."""

    class Meta:
        model = QCMQuestion
        fields = ['index', 'question', 'options']

    index = serializers.IntegerField(source='order_index')


class FormFieldSerializer(serializers.ModelSerializer):
    selectOptions = serializers.JSONField(source='select_options', allow_null=True)

    class Meta:
        model = FormFieldDef
        fields = ['id', 'label', 'type', 'required', 'selectOptions']


class AssetDetailSerializer(serializers.ModelSerializer):
    """Full asset detail — type-specific fields."""
    orderIndex = serializers.IntegerField(source='order_index')
    externalUrl = serializers.SerializerMethodField()
    isCompleted = serializers.SerializerMethodField()
    consigneText = serializers.SerializerMethodField()
    isAccepted = serializers.SerializerMethodField()
    passingScore = serializers.SerializerMethodField()
    lastScore = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    formFields = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ['id', 'type', 'title', 'description', 'externalUrl',
                  'orderIndex', 'isCompleted', 'consigneText', 'isAccepted',
                  'passingScore', 'lastScore', 'questions', 'formFields']

    def get_externalUrl(self, obj):
        return resolve_url(obj.external_url)

    def get_isCompleted(self, obj):
        user = self.context.get('user')
        if not user or obj.type == 'consigne':
            return None
        from apps.progress.models import AssetCompletion
        return AssetCompletion.objects.filter(user=user, asset=obj).exists()

    def get_consigneText(self, obj):
        if obj.type == 'consigne':
            return obj.consigne_text
        return None

    def get_isAccepted(self, obj):
        if obj.type != 'consigne':
            return None
        user = self.context.get('user')
        if not user:
            return False
        from apps.progress.models import ConsigneAcceptance
        return ConsigneAcceptance.objects.filter(user=user, step=obj.step).exists()

    def get_passingScore(self, obj):
        if obj.type == 'qcm':
            return obj.passing_score
        return None

    def get_lastScore(self, obj):
        if obj.type != 'qcm':
            return None
        user = self.context.get('user')
        if not user:
            return None
        from apps.progress.models import QCMAttempt
        attempt = QCMAttempt.objects.filter(
            user=user, asset=obj
        ).order_by('-attempted_at').first()
        return float(attempt.score) if attempt else None

    def get_questions(self, obj):
        if obj.type != 'qcm':
            return None
        return QCMQuestionSerializer(obj.questions.all(), many=True).data

    def get_formFields(self, obj):
        if obj.type != 'form':
            return None
        return FormFieldSerializer(obj.form_fields.all(), many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        t = instance.type
        # Remove irrelevant fields based on type
        if t != 'consigne':
            data.pop('consigneText', None)
            data.pop('isAccepted', None)
        if t != 'qcm':
            data.pop('passingScore', None)
            data.pop('lastScore', None)
            data.pop('questions', None)
        if t != 'form':
            data.pop('formFields', None)
        if t == 'consigne':
            data.pop('isCompleted', None)
        return data
