from django.test import TestCase
from apps.accounts.models import User
from apps.programs.models import Program
from apps.programs.models_assets import Asset, FormFieldDef
from apps.progress.models import FormSubmission
from apps.admin_api.serializers import AdminFormSubmissionRowSerializer


class AdminFormSubmissionRowSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+237600000001', password='pass', first_name='Alice', last_name='Dupont',
        )
        self.program = Program.objects.create(
            name='Prog Test',
            description='Test description',
            image_url='http://example.com/img.png',
            price=10000,
            duration_weeks=4,
            num_installments=2,
        )
        self.asset = Asset.objects.create(
            title='Formulaire test', type='form', program=self.program,
        )
        self.program.enrollment_form_asset_id = self.asset.id
        self.program.save()
        self.submission = FormSubmission.objects.create(
            id='sub_test001',
            user=self.user,
            asset=self.asset,
            responses=[{'fieldId': 'f1', 'value': 'Test'}],
        )

    def test_row_serializer_type_enrollment(self):
        enrollment_ids = {self.asset.id}
        data = AdminFormSubmissionRowSerializer(
            self.submission,
            context={'enrollment_asset_ids': enrollment_ids},
        ).data
        self.assertEqual(data['type'], 'enrollment')
        self.assertEqual(data['userName'], 'Alice Dupont')
        self.assertEqual(data['programTitle'], 'Prog Test')
        self.assertEqual(data['responseCount'], 1)


class AdminFormSubmissionDetailSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+237600000010', password='pass', first_name='Claire', last_name='Dupont',
        )
        self.program = Program.objects.create(
            name='Prog Detail',
            description='Test description',
            image_url='http://example.com/img.png',
            price=10000,
            duration_weeks=4,
            num_installments=2,
        )
        self.asset = Asset.objects.create(
            title='Form Detail', type='form', program=self.program,
        )
        FormFieldDef.objects.create(
            id='fd_label01', asset=self.asset, label='Votre objectif',
            type='text', required=True, order_index=0,
        )
        self.submission = FormSubmission.objects.create(
            id='sub_detail01',
            user=self.user,
            asset=self.asset,
            responses=[{'fieldId': 'fd_label01', 'value': 'Réduire le stress'}],
        )

    def test_responses_resolve_field_labels(self):
        from apps.admin_api.serializers import AdminFormSubmissionDetailSerializer
        from apps.progress.models import FormSubmission as FS
        sub = FS.objects.prefetch_related('asset__form_fields').get(id='sub_detail01')
        data = AdminFormSubmissionDetailSerializer(sub).data
        self.assertEqual(data['userName'], 'Claire Dupont')
        self.assertEqual(data['formTitle'], 'Form Detail')
        self.assertEqual(len(data['responses']), 1)
        self.assertEqual(data['responses'][0]['fieldLabel'], 'Votre objectif')
        self.assertEqual(data['responses'][0]['value'], 'Réduire le stress')

    def test_responses_fallback_to_field_id_when_no_matching_field_def(self):
        from apps.admin_api.serializers import AdminFormSubmissionDetailSerializer
        from apps.progress.models import FormSubmission as FS
        # Create submission with an unknown fieldId
        sub2 = FormSubmission.objects.create(
            id='sub_detail02',
            user=self.user,
            asset=self.asset,
            responses=[{'fieldId': 'unknown_field', 'value': 'Some value'}],
        )
        sub2 = FS.objects.prefetch_related('asset__form_fields').get(id='sub_detail02')
        data = AdminFormSubmissionDetailSerializer(sub2).data
        self.assertEqual(data['responses'][0]['fieldLabel'], 'unknown_field')
        self.assertEqual(data['responses'][0]['value'], 'Some value')
