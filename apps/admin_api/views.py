# Re-export all admin views — urls.py uses `from . import views` and accesses views.*
from .views_programs import (
    AdminProgramViewSet,
    AdminDegreeViewSet,
    AdminStepViewSet,
    AdminAssetViewSet,
    AdminQCMQuestionViewSet,
    AdminFormFieldViewSet,
    AdminDegreeFileViewSet,
    AdminPriseDeContactViewSet,
    AdminPdcAssetViewSet,
)
from .views_sessions import AdminSessionViewSet
from .views_users import AdminUserViewSet
from .views_enrollments import AdminEnrollmentViewSet, AdminPaymentViewSet
from .views_content import (
    AdminTestimonyViewSet,
    AdminTestimonyCommentViewSet,
    AdminFAQViewSet,
    AdminContactInfoView,
    AdminContactSubmissionViewSet,
    AdminPromoCodeViewSet,
    AdminAppSettingsView,
)
from .views_upload import AdminFileUploadView
from .views_stats import (
    AdminStatsOverviewView,
    AdminEnrollmentTrendsView,
    AdminRevenueTrendsView,
    AdminCompletionStatsView,
)
from .views_progress import (
    AdminUserProgressView,
    AdminProgressStatsView,
    AdminProgressExportView,
)
from .views_mandataires import AdminMandataireListView
