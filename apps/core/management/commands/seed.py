import math
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.content.models import ContactInfo, FAQItem
from apps.enrollments.models import Enrollment, Payment
from apps.programs.models import Asset, Degree, FormFieldDef, Program, QCMQuestion, Step
from apps.progress.models import (
    AssetCompletion,
    ConsigneAcceptance,
    QCMAttempt,
    StepProgress,
)
from apps.sessions.models import LiveReplaySession
from apps.testimonies.models import Testimony, TestimonyComment, TestimonyReaction


class Command(BaseCommand):
    help = 'Seed the database with test data matching the Flutter mock data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        self._create_users()
        self._create_programs()
        self._create_enrollments()
        self._create_progress()
        self._create_sessions()
        self._create_testimonies()
        self._create_faq()
        self._create_contact()

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    def _create_users(self):
        self.stdout.write('  Creating users...')

        self.user1, _ = User.objects.get_or_create(
            id='usr_test_001',
            defaults={
                'first_name': 'Jean',
                'last_name': 'Dupont',
                'phone': '+22507000000',
                'email': 'jean.dupont@example.com',
                'date_of_birth': '1990-05-15',
                'city': 'Abidjan',
                'country': "Cote d'Ivoire",
            }
        )
        self.user1.set_password('Test1234')
        self.user1.save()

        self.user2, _ = User.objects.get_or_create(
            id='user_2',
            defaults={
                'first_name': 'Marie',
                'last_name': 'Kouassi',
                'phone': '+22507000001',
                'city': 'Abidjan',
                'country': "Cote d'Ivoire",
            }
        )
        self.user2.set_password('Test1234')
        self.user2.save()

        self.user3, _ = User.objects.get_or_create(
            id='user_3',
            defaults={
                'first_name': 'Amadou',
                'last_name': 'Diallo',
                'phone': '+22507000002',
                'city': 'Abidjan',
                'country': "Cote d'Ivoire",
            }
        )
        self.user3.set_password('Test1234')
        self.user3.save()

        self.user4, _ = User.objects.get_or_create(
            id='user_4',
            defaults={
                'first_name': 'Fatou',
                'last_name': 'Bamba',
                'phone': '+22507000003',
                'city': 'Yamoussoukro',
                'country': "Cote d'Ivoire",
            }
        )
        self.user4.set_password('Test1234')
        self.user4.save()

        self.user5, _ = User.objects.get_or_create(
            id='user_5',
            defaults={
                'first_name': 'Kouame',
                'last_name': 'Assi',
                'phone': '+22507000004',
                'city': 'Bouake',
                'country': "Cote d'Ivoire",
            }
        )
        self.user5.set_password('Test1234')
        self.user5.save()

    def _create_programs(self):
        self.stdout.write('  Creating programs...')

        # ========== PROGRAM LIMITLESS ==========
        self.prog_limitless, _ = Program.objects.get_or_create(
            id='prog_limitless',
            defaults={
                'name': 'Programme Limitless',
                'description': 'Programme complet de developpement personnel et professionnel. '
                               'Transformez votre mindset et atteignez vos objectifs.',
                'image_url': 'https://images.unsplash.com/photo-1631879742103-0e652e04b3e1?w=800',
                'price': 150000,
                'duration_weeks': 8,
                'presentation_video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            }
        )

        # Degree 1
        deg_lim_1, _ = Degree.objects.get_or_create(
            id='deg_lim_1',
            defaults={
                'program': self.prog_limitless,
                'title': 'Niveau 1: Fondations du Mindset',
                'description': "Posez les bases d'un etat d'esprit gagnant et productif",
                'order_index': 0,
            }
        )

        # Step 1.1
        step_lim_1_1, _ = Step.objects.get_or_create(
            id='step_lim_1_1',
            defaults={
                'degree': deg_lim_1,
                'title': 'Etape 1: Introduction au Mindset',
                'description': 'Decouvrez les principes fondamentaux du mindset',
                'order_index': 0,
            }
        )
        self._create_step_assets_lim_1_1(step_lim_1_1)

        # Step 1.2
        step_lim_1_2, _ = Step.objects.get_or_create(
            id='step_lim_1_2',
            defaults={
                'degree': deg_lim_1,
                'title': 'Etape 2: Vaincre les Croyances Limitantes',
                'description': 'Identifiez et surmontez vos croyances qui vous freinent',
                'order_index': 1,
            }
        )
        self._create_step_assets_lim_1_2(step_lim_1_2)

        # Degree 2
        deg_lim_2, _ = Degree.objects.get_or_create(
            id='deg_lim_2',
            defaults={
                'program': self.prog_limitless,
                'title': 'Niveau 2: Productivite et Action',
                'description': 'Maitrisez votre temps et passez a l\'action',
                'order_index': 1,
            }
        )

        step_lim_2_1, _ = Step.objects.get_or_create(
            id='step_lim_2_1',
            defaults={
                'degree': deg_lim_2,
                'title': 'Etape 1: Gestion du Temps',
                'description': 'Apprenez les techniques de gestion du temps efficaces',
                'order_index': 0,
            }
        )
        self._create_generic_step_assets(step_lim_2_1, 'lim_2_1')

        step_lim_2_2, _ = Step.objects.get_or_create(
            id='step_lim_2_2',
            defaults={
                'degree': deg_lim_2,
                'title': 'Etape 2: Passage a l\'Action',
                'description': 'Techniques pour vaincre la procrastination',
                'order_index': 1,
            }
        )
        self._create_generic_step_assets(step_lim_2_2, 'lim_2_2')

        # Degree 3
        deg_lim_3, _ = Degree.objects.get_or_create(
            id='deg_lim_3',
            defaults={
                'program': self.prog_limitless,
                'title': 'Niveau 3: Excellence et Vision',
                'description': "Definissez votre vision et visez l'excellence",
                'order_index': 2,
            }
        )

        step_lim_3_1, _ = Step.objects.get_or_create(
            id='step_lim_3_1',
            defaults={
                'degree': deg_lim_3,
                'title': 'Etape 1: Vision et Excellence',
                'description': 'Construisez votre vision personnelle',
                'order_index': 0,
            }
        )
        self._create_generic_step_assets(step_lim_3_1, 'lim_3_1')

        # ========== PROGRAM PMS ==========
        self.prog_pms, _ = Program.objects.get_or_create(
            id='prog_pms',
            defaults={
                'name': 'Programme PMS',
                'description': 'Programme de Management Strategique pour les leaders.',
                'image_url': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800',
                'price': 120000,
                'duration_weeks': 6,
                'presentation_video_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
            }
        )

        deg_pms_1, _ = Degree.objects.get_or_create(
            id='deg_pms_1',
            defaults={
                'program': self.prog_pms,
                'title': 'Niveau 1: Leadership Fondamental',
                'description': 'Les bases du leadership personnel',
                'order_index': 0,
            }
        )
        step_pms_1_1, _ = Step.objects.get_or_create(
            id='step_pms_1_1',
            defaults={
                'degree': deg_pms_1,
                'title': 'Etape 1: Decouverte du Leadership',
                'description': 'Introduction aux principes du leadership',
                'order_index': 0,
            }
        )
        self._create_generic_step_assets(step_pms_1_1, 'pms_1_1')

        step_pms_1_2, _ = Step.objects.get_or_create(
            id='step_pms_1_2',
            defaults={
                'degree': deg_pms_1,
                'title': 'Etape 2: Communication Efficace',
                'description': 'Maitrisez l\'art de la communication',
                'order_index': 1,
            }
        )
        self._create_generic_step_assets(step_pms_1_2, 'pms_1_2')

        deg_pms_2, _ = Degree.objects.get_or_create(
            id='deg_pms_2',
            defaults={
                'program': self.prog_pms,
                'title': 'Niveau 2: Management Avance',
                'description': 'Techniques avancees de management',
                'order_index': 1,
            }
        )
        step_pms_2_1, _ = Step.objects.get_or_create(
            id='step_pms_2_1',
            defaults={
                'degree': deg_pms_2,
                'title': 'Etape 1: Strategie et Decision',
                'description': 'Prise de decision strategique',
                'order_index': 0,
            }
        )
        self._create_generic_step_assets(step_pms_2_1, 'pms_2_1')

        # ========== PROGRAM BOOST ==========
        self.prog_boost, _ = Program.objects.get_or_create(
            id='prog_boost',
            defaults={
                'name': 'Programme Boost Entrepreneur',
                'description': 'Lancez votre entreprise avec les bonnes bases.',
                'image_url': 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800',
                'price': 200000,
                'duration_weeks': 10,
            }
        )

        deg_boost_1, _ = Degree.objects.get_or_create(
            id='deg_boost_1',
            defaults={
                'program': self.prog_boost,
                'title': 'Niveau 1: Idee et Validation',
                'description': 'Validez votre idee de business',
                'order_index': 0,
            }
        )
        step_boost_1_1, _ = Step.objects.get_or_create(
            id='step_boost_1_1',
            defaults={
                'degree': deg_boost_1,
                'title': 'Etape 1: Trouver son Idee',
                'description': 'Methodes pour identifier des opportunites',
                'order_index': 0,
            }
        )
        self._create_generic_step_assets(step_boost_1_1, 'boost_1_1')

        deg_boost_2, _ = Degree.objects.get_or_create(
            id='deg_boost_2',
            defaults={
                'program': self.prog_boost,
                'title': 'Niveau 2: Business Plan',
                'description': 'Construisez votre plan d\'affaires',
                'order_index': 1,
            }
        )
        step_boost_2_1, _ = Step.objects.get_or_create(
            id='step_boost_2_1',
            defaults={
                'degree': deg_boost_2,
                'title': 'Etape 1: Rediger son Business Plan',
                'description': 'Les composantes d\'un business plan solide',
                'order_index': 0,
            }
        )
        self._create_generic_step_assets(step_boost_2_1, 'boost_2_1')

        # ========== PROGRAM FINANCE ==========
        self.prog_finance, _ = Program.objects.get_or_create(
            id='prog_finance',
            defaults={
                'name': 'Programme Finance Personnelle',
                'description': 'Maitrisez vos finances et investissez intelligemment.',
                'image_url': 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800',
                'price': 100000,
                'duration_weeks': 4,
            }
        )

        deg_fin_1, _ = Degree.objects.get_or_create(
            id='deg_fin_1',
            defaults={
                'program': self.prog_finance,
                'title': 'Niveau 1: Budget et Epargne',
                'description': 'Les fondamentaux de la gestion financiere',
                'order_index': 0,
            }
        )
        step_fin_1_1, _ = Step.objects.get_or_create(
            id='step_fin_1_1',
            defaults={
                'degree': deg_fin_1,
                'title': 'Etape 1: Creer son Budget',
                'description': 'Apprenez a etablir un budget efficace',
                'order_index': 0,
            }
        )
        self._create_generic_step_assets(step_fin_1_1, 'fin_1_1')

    def _create_step_assets_lim_1_1(self, step):
        """Create specific assets for step_lim_1_1 matching API spec examples."""
        Asset.objects.get_or_create(
            id='asset_lim_1_1_consigne',
            defaults={
                'step': step, 'type': 'consigne',
                'title': "Consignes de l'etape",
                'order_index': 0,
                'consigne_text': 'Bienvenue dans cette premiere etape ! Avant de commencer, '
                                 'prenez un moment pour vous concentrer. Lisez attentivement '
                                 'chaque ressource et completez le QCM a la fin.',
            }
        )

        Asset.objects.get_or_create(
            id='asset_lim_1_1_video',
            defaults={
                'step': step, 'type': 'video',
                'title': 'Introduction au Mindset de Croissance',
                'description': 'Decouvrez comment transformer votre facon de penser',
                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                'order_index': 1,
            }
        )

        Asset.objects.get_or_create(
            id='asset_lim_1_1_pdf',
            defaults={
                'step': step, 'type': 'pdf',
                'title': 'Guide du Mindset - PDF',
                'description': 'Document de reference sur les principes cles',
                'external_url': 'https://example.com/mindset-guide.pdf',
                'order_index': 2,
            }
        )

        qcm_asset, _ = Asset.objects.get_or_create(
            id='asset_lim_1_1_qcm',
            defaults={
                'step': step, 'type': 'qcm',
                'title': 'QCM - Mindset de base',
                'order_index': 3,
                'passing_score': 70,
            }
        )

        questions = [
            {
                'question': "Qu'est-ce qu'un mindset de croissance ?",
                'options': [
                    'Croire que les capacites sont fixes',
                    'Croire que les capacites peuvent etre developpees',
                    'Eviter les defis',
                    'Se comparer aux autres',
                ],
                'correct_index': 1,
            },
            {
                'question': "Quelle est la premiere etape pour vaincre une croyance limitante ?",
                'options': [
                    "L'ignorer completement",
                    "L'identifier et la reconnaitre",
                    'Abandonner ses objectifs',
                    'Blamer les autres',
                ],
                'correct_index': 1,
            },
            {
                'question': "Comment developpe-t-on un mindset de reussite ?",
                'options': [
                    'En restant dans sa zone de confort',
                    'En evitant les erreurs',
                    "Par la pratique et l'apprentissage continu",
                    'En attendant la chance',
                ],
                'correct_index': 2,
            },
        ]

        for i, q in enumerate(questions):
            QCMQuestion.objects.get_or_create(
                asset=qcm_asset,
                order_index=i,
                defaults={
                    'question': q['question'],
                    'options': q['options'],
                    'correct_index': q['correct_index'],
                }
            )

    def _create_step_assets_lim_1_2(self, step):
        """Create assets for step_lim_1_2 with a form asset."""
        Asset.objects.get_or_create(
            id='asset_lim_1_2_consigne',
            defaults={
                'step': step, 'type': 'consigne',
                'title': "Consignes de l'etape",
                'order_index': 0,
                'consigne_text': 'Dans cette etape, vous allez identifier vos croyances limitantes. '
                                 'Soyez honnete avec vous-meme et prenez le temps de reflechir.',
            }
        )

        Asset.objects.get_or_create(
            id='asset_lim_1_2_video',
            defaults={
                'step': step, 'type': 'video',
                'title': 'Comprendre les Croyances Limitantes',
                'description': 'Video explicative sur les mecanismes des croyances',
                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'order_index': 1,
            }
        )

        Asset.objects.get_or_create(
            id='asset_lim_1_2_audio',
            defaults={
                'step': step, 'type': 'audio',
                'title': 'Meditation Guidee - Liberation',
                'description': 'Meditation pour se liberer des croyances negatives',
                'external_url': 'https://example.com/meditation.mp3',
                'order_index': 2,
            }
        )

        form_asset, _ = Asset.objects.get_or_create(
            id='asset_lim_1_2_form',
            defaults={
                'step': step, 'type': 'form',
                'title': 'Auto-evaluation',
                'description': 'Evaluez vos croyances limitantes',
                'order_index': 3,
            }
        )

        form_fields = [
            {'id': 'f1', 'label': 'Quelle est votre croyance limitante principale ?',
             'type': 'textarea', 'required': True},
            {'id': 'f2', 'label': 'Comment comptez-vous la surmonter ?',
             'type': 'textarea', 'required': True},
            {'id': 'f3', 'label': 'Votre email pour le suivi',
             'type': 'email', 'required': False},
        ]

        for i, f in enumerate(form_fields):
            FormFieldDef.objects.get_or_create(
                id=f['id'],
                defaults={
                    'asset': form_asset,
                    'label': f['label'],
                    'type': f['type'],
                    'required': f['required'],
                    'order_index': i,
                }
            )

        qcm_asset, _ = Asset.objects.get_or_create(
            id='asset_lim_1_2_qcm',
            defaults={
                'step': step, 'type': 'qcm',
                'title': 'QCM - Croyances Limitantes',
                'order_index': 4,
                'passing_score': 70,
            }
        )

        questions = [
            {
                'question': "Qu'est-ce qu'une croyance limitante ?",
                'options': [
                    'Une pensee positive',
                    'Une conviction qui freine notre potentiel',
                    'Un fait scientifique',
                    'Une opinion des autres',
                ],
                'correct_index': 1,
            },
            {
                'question': 'Comment identifier une croyance limitante ?',
                'options': [
                    'En ignorant ses pensees',
                    'En observant ses reactions automatiques',
                    'En evitant la reflexion',
                    'En demandant aux autres',
                ],
                'correct_index': 1,
            },
        ]

        for i, q in enumerate(questions):
            QCMQuestion.objects.get_or_create(
                asset=qcm_asset,
                order_index=i,
                defaults={
                    'question': q['question'],
                    'options': q['options'],
                    'correct_index': q['correct_index'],
                }
            )

    def _create_generic_step_assets(self, step, prefix):
        """Create a standard set of assets for a step."""
        Asset.objects.get_or_create(
            id=f'asset_{prefix}_consigne',
            defaults={
                'step': step, 'type': 'consigne',
                'title': "Consignes de l'etape",
                'order_index': 0,
                'consigne_text': f'Bienvenue dans cette etape. Suivez les instructions attentivement.',
            }
        )

        Asset.objects.get_or_create(
            id=f'asset_{prefix}_video',
            defaults={
                'step': step, 'type': 'video',
                'title': f'Video - {step.title}',
                'description': 'Contenu video de cette etape',
                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'order_index': 1,
            }
        )

        Asset.objects.get_or_create(
            id=f'asset_{prefix}_pdf',
            defaults={
                'step': step, 'type': 'pdf',
                'title': f'Support PDF - {step.title}',
                'description': 'Document de support',
                'external_url': 'https://example.com/doc.pdf',
                'order_index': 2,
            }
        )

        qcm_asset, _ = Asset.objects.get_or_create(
            id=f'asset_{prefix}_qcm',
            defaults={
                'step': step, 'type': 'qcm',
                'title': f'QCM - {step.title}',
                'order_index': 3,
                'passing_score': 70,
            }
        )

        QCMQuestion.objects.get_or_create(
            asset=qcm_asset,
            order_index=0,
            defaults={
                'question': "Quelle est la reponse correcte ?",
                'options': ['Option A', 'Option B (correcte)', 'Option C', 'Option D'],
                'correct_index': 1,
            }
        )
        QCMQuestion.objects.get_or_create(
            asset=qcm_asset,
            order_index=1,
            defaults={
                'question': "Quel concept est le plus important ?",
                'options': ['Concept 1', 'Concept 2', 'Concept 3 (correct)', 'Concept 4'],
                'correct_index': 2,
            }
        )

    def _create_enrollments(self):
        self.stdout.write('  Creating enrollments...')

        now = timezone.now()

        # Enrollment 1: user1 in Limitless, full payment completed
        self.enr1, _ = Enrollment.objects.get_or_create(
            id='enr_001',
            defaults={
                'program': self.prog_limitless,
                'user': self.user1,
                'payment_type': 'full',
                'payment_status': 'completed',
                'amount_paid': 150000,
                'total_amount': 150000,
            }
        )

        Payment.objects.get_or_create(
            id='pay_1',
            defaults={
                'enrollment': self.enr1,
                'amount': 150000,
                'method': 'orangeMoney',
                'status': 'completed',
                'transaction_ref': 'txn_mock_001',
                'mf_transaction_id': 'txn_mock_001',
            }
        )

        # Enrollment 2: user1 in PMS, installment, partial
        self.enr2, _ = Enrollment.objects.get_or_create(
            id='enr_002',
            defaults={
                'program': self.prog_pms,
                'user': self.user1,
                'payment_type': 'installment',
                'payment_status': 'partial',
                'amount_paid': 60000,
                'total_amount': 120000,
            }
        )

        Payment.objects.get_or_create(
            id='pay_2',
            defaults={
                'enrollment': self.enr2,
                'amount': 60000,
                'method': 'mtnMoney',
                'status': 'completed',
                'transaction_ref': 'txn_mock_002',
                'mf_transaction_id': 'txn_mock_002',
            }
        )

    def _create_progress(self):
        self.stdout.write('  Creating progress...')

        # Limitless: step 1.1 completed, step 1.2 available, rest locked
        steps_limitless = [
            ('step_lim_1_1', 'completed'),
            ('step_lim_1_2', 'available'),
            ('step_lim_2_1', 'locked'),
            ('step_lim_2_2', 'locked'),
            ('step_lim_3_1', 'locked'),
        ]

        for step_id, step_status in steps_limitless:
            try:
                step = Step.objects.get(id=step_id)
                StepProgress.objects.get_or_create(
                    user=self.user1,
                    step=step,
                    defaults={
                        'program': self.prog_limitless,
                        'status': step_status,
                    }
                )
            except Step.DoesNotExist:
                pass

        # Mark all assets in step_lim_1_1 as completed
        step_1_1_assets = Asset.objects.filter(step_id='step_lim_1_1')
        for asset in step_1_1_assets:
            if asset.type in ('pdf', 'audio', 'video'):
                AssetCompletion.objects.get_or_create(
                    user=self.user1,
                    asset=asset,
                    defaults={'program': self.prog_limitless}
                )
            elif asset.type == 'qcm':
                QCMAttempt.objects.get_or_create(
                    user=self.user1,
                    asset=asset,
                    defaults={
                        'score': 100.0,
                        'passed': True,
                        'answers': [
                            {'questionIndex': 0, 'selectedOptionIndex': 1},
                            {'questionIndex': 1, 'selectedOptionIndex': 1},
                            {'questionIndex': 2, 'selectedOptionIndex': 2},
                        ],
                    }
                )
                AssetCompletion.objects.get_or_create(
                    user=self.user1,
                    asset=asset,
                    defaults={'program': self.prog_limitless}
                )

        # Consigne accepted for step 1.1
        try:
            step_obj = Step.objects.get(id='step_lim_1_1')
            ConsigneAcceptance.objects.get_or_create(
                user=self.user1, step=step_obj
            )
        except Step.DoesNotExist:
            pass

        # PMS: step_pms_1_1 available, rest locked
        steps_pms = [
            ('step_pms_1_1', 'available'),
            ('step_pms_1_2', 'locked'),
            ('step_pms_2_1', 'locked'),
        ]
        for step_id, step_status in steps_pms:
            try:
                step = Step.objects.get(id=step_id)
                StepProgress.objects.get_or_create(
                    user=self.user1,
                    step=step,
                    defaults={
                        'program': self.prog_pms,
                        'status': step_status,
                    }
                )
            except Step.DoesNotExist:
                pass

    def _create_sessions(self):
        self.stdout.write('  Creating sessions...')

        now = timezone.now()

        sessions = [
            {
                'id': 'live_1',
                'title': 'Live - Revision Mindset',
                'description': 'Session de revision interactive sur les principes du mindset de croissance',
                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'date': now + timedelta(days=2),
                'duration_minutes': 90,
                'is_live': True,
            },
            {
                'id': 'live_2',
                'title': 'Live - Atelier Leadership',
                'description': 'Atelier pratique sur le leadership au quotidien',
                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                'date': now + timedelta(days=9),
                'duration_minutes': 120,
                'is_live': True,
            },
            {
                'id': 'replay_1',
                'title': 'Replay - Mindset de Croissance',
                'description': 'Revisionnez la session complete sur le mindset de croissance',
                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                'date': now - timedelta(days=7),
                'duration_minutes': 90,
                'is_live': False,
            },
            {
                'id': 'replay_2',
                'title': 'Replay - Gestion du Stress',
                'description': 'Techniques de gestion du stress pour professionnels',
                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'date': now - timedelta(days=14),
                'duration_minutes': 60,
                'is_live': False,
            },
            {
                'id': 'replay_3',
                'title': 'Replay - Communication Non Violente',
                'description': 'Les bases de la communication non violente',
                'external_url': 'https://vimeo.com/76979871',
                'date': now - timedelta(days=21),
                'duration_minutes': 75,
                'is_live': False,
            },
            {
                'id': 'replay_4',
                'title': 'Replay - Atelier Leadership',
                'description': 'Les bases du leadership personnel et comment inspirer les autres',
                'external_url': 'https://vimeo.com/76979871',
                'date': now - timedelta(days=30),
                'duration_minutes': 120,
                'is_live': False,
            },
        ]

        for s in sessions:
            LiveReplaySession.objects.get_or_create(id=s['id'], defaults=s)

    def _create_testimonies(self):
        self.stdout.write('  Creating testimonies...')

        now = timezone.now()

        testimonies_data = [
            {
                'id': 'test_1', 'author': self.user2,
                'content': 'Grace au Programme Limitless, j\'ai completement transforme '
                           'ma facon de penser. Les exercices pratiques et les QCM m\'ont aide '
                           'a vraiment comprendre chaque concept.',
                'like_count': 12, 'heart_count': 8, 'comment_count': 2,
            },
            {
                'id': 'test_2', 'author': self.user3,
                'content': 'Le Programme PMS m\'a donne les outils necessaires pour devenir '
                           'un meilleur leader. Je recommande vivement !',
                'like_count': 8, 'heart_count': 5, 'comment_count': 0,
            },
            {
                'id': 'test_3', 'author': self.user4,
                'content': 'Excellent contenu ! Les videos sont claires et les QCM '
                           'permettent de verifier ses connaissances. Merci Booster Week !',
                'like_count': 15, 'heart_count': 10, 'comment_count': 1,
            },
            {
                'id': 'test_4', 'author': self.user5,
                'content': 'J\'ai suivi le programme Finance Personnelle et j\'ai enfin '
                           'compris comment gerer mon budget. Un investissement qui vaut le coup.',
                'like_count': 6, 'heart_count': 3, 'comment_count': 0,
            },
            {
                'id': 'test_5', 'author': self.user2,
                'content': 'Le support de l\'equipe est exceptionnel. Chaque question '
                           'recoit une reponse rapide et pertinente.',
                'like_count': 4, 'heart_count': 7, 'comment_count': 1,
            },
        ]

        for t in testimonies_data:
            Testimony.objects.get_or_create(
                id=t['id'],
                defaults={
                    'author': t['author'],
                    'content': t['content'],
                    'like_count': t['like_count'],
                    'heart_count': t['heart_count'],
                    'comment_count': t['comment_count'],
                }
            )

        # Comments
        TestimonyComment.objects.get_or_create(
            id='com_1',
            defaults={
                'testimony_id': 'test_1',
                'author': self.user3,
                'content': "Tout a fait d'accord Marie ! Le programme a change ma vie aussi.",
            }
        )
        TestimonyComment.objects.get_or_create(
            id='com_2',
            defaults={
                'testimony_id': 'test_1',
                'author': self.user4,
                'content': 'Merci pour ce temoignage inspirant !',
            }
        )
        TestimonyComment.objects.get_or_create(
            id='com_3',
            defaults={
                'testimony_id': 'test_3',
                'author': self.user5,
                'content': 'Je confirme, les QCM sont tres bien faits.',
            }
        )
        TestimonyComment.objects.get_or_create(
            id='com_4',
            defaults={
                'testimony_id': 'test_5',
                'author': self.user3,
                'content': "L'equipe est vraiment a l'ecoute.",
            }
        )

        # Some reactions
        for user in [self.user1, self.user3, self.user4]:
            TestimonyReaction.objects.get_or_create(
                testimony_id='test_1', user=user, reaction_type='like',
            )

    def _create_faq(self):
        self.stdout.write('  Creating FAQ...')

        faqs = [
            {
                'question': "Comment fonctionne le paiement ?",
                'answer': "Vous pouvez payer en une seule fois ou en 2 versements via "
                          "Orange Money, MTN Money ou Wave. Le premier versement donne "
                          "acces a la premiere moitie du programme.",
            },
            {
                'question': "Puis-je acceder au contenu hors ligne ?",
                'answer': "Les videos et audios necessitent une connexion internet. "
                          "Les documents PDF peuvent etre telecharges pour une consultation hors ligne.",
            },
            {
                'question': "Comment fonctionne le systeme de niveaux ?",
                'answer': "Chaque programme est divise en niveaux (degrees) contenant des etapes. "
                          "Vous devez completer chaque etape (videos, QCM, formulaires) "
                          "pour debloquer la suivante.",
            },
            {
                'question': "Que se passe-t-il si j'echoue a un QCM ?",
                'answer': "Vous pouvez retenter le QCM autant de fois que necessaire. "
                          "Il faut obtenir au moins 70% pour valider l'etape.",
            },
            {
                'question': "Comment contacter le support ?",
                'answer': "Vous pouvez nous contacter via WhatsApp, email ou telephone. "
                          "Consultez la page Contact pour les details.",
            },
        ]

        for i, faq in enumerate(faqs):
            FAQItem.objects.get_or_create(
                question=faq['question'],
                defaults={
                    'answer': faq['answer'],
                    'order_index': i,
                }
            )

    def _create_contact(self):
        self.stdout.write('  Creating contact info...')

        ContactInfo.objects.get_or_create(
            id=1,
            defaults={
                'phone': '+22507000000',
                'email': 'contact@boosterweek.com',
                'whatsapp': '+22507000000',
            }
        )
