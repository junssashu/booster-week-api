from django.test import TestCase
from rest_framework.test import APIClient
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


class AdminFormSubmissionListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            phone='+237600000020', password='pass',
            first_name='Admin', last_name='User', role='admin',
        )
        self.client.force_authenticate(user=self.admin)

        self.program = Program.objects.create(
            name='Prog View Test',
            description='Test description',
            image_url='http://example.com/img.png',
            price=10000,
            duration_weeks=4,
            num_installments=2,
        )
        self.asset = Asset.objects.create(title='Form A', type='form', program=self.program)
        self.program.enrollment_form_asset_id = self.asset.id
        self.program.save()

        self.student = User.objects.create_user(
            phone='+237600000021', password='pass',
            first_name='Bob', last_name='Martin',
        )
        FormSubmission.objects.create(
            id='sub_view001',
            user=self.student, asset=self.asset,
            responses=[{'fieldId': 'f1', 'value': 'Oui'}],
        )

    def test_list_returns_submission(self):
        response = self.client.get('/api/v1/admin/form-submissions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data['data'])
        self.assertEqual(len(data['data']['results']), 1)
        row = data['data']['results'][0]
        self.assertEqual(row['type'], 'enrollment')
        self.assertEqual(row['userName'], 'Bob Martin')

    def test_list_filters_by_type_in_course(self):
        response = self.client.get('/api/v1/admin/form-submissions/?type=in-course')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['data']['results']), 0)

    def test_detail_resolves_field_labels(self):
        FormFieldDef.objects.create(
            id='f1', asset=self.asset, label='Votre objectif', type='text',
            required=True, order_index=0,
        )
        sub = FormSubmission.objects.get(id='sub_view001')
        response = self.client.get(f'/api/v1/admin/form-submissions/{sub.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['responses'][0]['fieldLabel'], 'Votre objectif')
        self.assertEqual(data['data']['responses'][0]['value'], 'Oui')
