from django.test import TestCase
from apps.accounts.models import User
from apps.programs.models import Program
from apps.programs.models_assets import Asset
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
