import math
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.content.models import ContactInfo, FAQItem
from apps.enrollments.models import Enrollment, Payment
from apps.programs.models import Asset, Degree, DegreeFile, FormFieldDef, Program, QCMQuestion, Step
from apps.progress.models import (
    AssetCompletion,
    ConsigneAcceptance,
    QCMAttempt,
    StepProgress,
)
from apps.sessions.models import LiveReplaySession, SessionAttendance
from apps.testimonies.models import Testimony, TestimonyComment, TestimonyReaction


# ────────────────────────────────────────────────────────────────
# DATA DEFINITIONS
# ────────────────────────────────────────────────────────────────

PROGRAMS_DATA = [
    # ═══════════════ PROGRAMME LIMITLESS ═══════════════
    {
        'id': 'prog_limitless',
        'name': 'Programme Limitless',
        'description': (
            'Programme complet de developpement personnel et professionnel. '
            'Transformez votre mindset et atteignez vos objectifs. '
            'A travers 3 niveaux progressifs, vous apprendrez a maitriser '
            'votre etat d\'esprit, booster votre productivite et viser l\'excellence.'
        ),
        'image_url': 'https://images.unsplash.com/photo-1552664730-d307ca884978?w=800',
        'price': 150000,
        'duration_weeks': 8,
        'presentation_video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'degrees': [
            {
                'id': 'deg_lim_1',
                'title': 'Niveau 1: Fondations du Mindset',
                'description': "Posez les bases d'un etat d'esprit gagnant et productif",
                'order_index': 0,
                'files': [
                    {
                        'id': 'dfile_lim_1_1', 'type': 'pdf',
                        'title': 'Fiche Recap - Fondations du Mindset',
                        'description': 'Resume des concepts cles du Niveau 1',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_lim_1_2', 'type': 'audio',
                        'title': 'Podcast Bonus - Motivation Quotidienne',
                        'description': 'Un podcast pour rester motive tout au long du niveau',
                        'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_lim_1_1',
                        'title': 'Introduction au Mindset',
                        'description': 'Decouvrez les principes fondamentaux du mindset de croissance',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_lim_1_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Bienvenue dans cette premiere etape ! Avant de commencer, '
                                    'prenez un moment pour vous concentrer. Lisez attentivement '
                                    'chaque ressource et completez le QCM a la fin. '
                                    'Objectif : comprendre la difference entre un mindset fixe '
                                    'et un mindset de croissance.'
                                ),
                            },
                            {
                                'id': 'asset_lim_1_1_video', 'type': 'video',
                                'title': 'Introduction au Mindset de Croissance',
                                'description': 'Decouvrez comment transformer votre facon de penser',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_1_1_pdf', 'type': 'pdf',
                                'title': 'Guide du Mindset - PDF',
                                'description': 'Document de reference sur les principes cles du mindset',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_1_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Mindset de base',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': "Qu'est-ce qu'un mindset de croissance ?",
                                        'options': [
                                            'Croire que les capacites sont fixes et immuables',
                                            'Croire que les capacites peuvent etre developpees par l\'effort',
                                            'Eviter les defis pour ne pas echouer',
                                            'Se comparer constamment aux autres',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': "Quelle attitude caracterise un mindset fixe ?",
                                        'options': [
                                            'Accueillir les critiques constructives',
                                            'Voir l\'effort comme un chemin vers la maitrise',
                                            'Abandonner face aux obstacles difficiles',
                                            'S\'inspirer du succes des autres',
                                        ],
                                        'correct_index': 2,
                                    },
                                    {
                                        'question': "Comment developpe-t-on un mindset de reussite ?",
                                        'options': [
                                            'En restant dans sa zone de confort',
                                            'En evitant les erreurs a tout prix',
                                            'Par la pratique deliberee et l\'apprentissage continu',
                                            'En attendant que la motivation vienne',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_lim_1_2',
                        'title': 'Vaincre les Croyances Limitantes',
                        'description': 'Identifiez et surmontez vos croyances qui vous freinent',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_lim_1_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Dans cette etape, vous allez identifier vos croyances limitantes. '
                                    'Soyez honnete avec vous-meme et prenez le temps de reflechir. '
                                    'Ecoutez la meditation guidee dans un endroit calme.'
                                ),
                            },
                            {
                                'id': 'asset_lim_1_2_video', 'type': 'video',
                                'title': 'Comprendre les Croyances Limitantes',
                                'description': 'Video explicative sur les mecanismes des croyances',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_1_2_audio', 'type': 'audio',
                                'title': 'Meditation Guidee - Liberation',
                                'description': 'Meditation pour se liberer des croyances negatives (15 min)',
                                'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_1_2_form', 'type': 'form',
                                'title': 'Auto-evaluation des Croyances',
                                'description': 'Evaluez vos croyances limitantes personnelles',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_lim12_1', 'label': 'Quelle est votre croyance limitante principale ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_lim12_2', 'label': 'Depuis quand avez-vous cette croyance ?', 'type': 'text', 'required': True},
                                    {'id': 'f_lim12_3', 'label': 'Comment comptez-vous la surmonter ?', 'type': 'textarea', 'required': True},
                                ],
                            },
                            {
                                'id': 'asset_lim_1_2_qcm', 'type': 'qcm',
                                'title': 'QCM - Croyances Limitantes',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': "Qu'est-ce qu'une croyance limitante ?",
                                        'options': [
                                            'Une pensee positive qui nous motive',
                                            'Une conviction profonde qui freine notre potentiel',
                                            'Un fait scientifique prouve',
                                            'Une opinion que les autres ont de nous',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle est la premiere etape pour vaincre une croyance limitante ?',
                                        'options': [
                                            'L\'ignorer completement',
                                            'L\'identifier et la reconnaitre consciemment',
                                            'Abandonner ses objectifs',
                                            'Blamer son entourage',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_lim_1_3',
                        'title': 'Le Pouvoir des Habitudes',
                        'description': 'Comprenez comment les habitudes faconnent votre vie et apprenez a en creer de nouvelles',
                        'order_index': 2,
                        'assets': [
                            {
                                'id': 'asset_lim_1_3_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Les habitudes representent 40% de nos actions quotidiennes. '
                                    'Dans cette etape, vous decouvrirez la boucle des habitudes '
                                    'et comment installer des routines positives durables.'
                                ),
                            },
                            {
                                'id': 'asset_lim_1_3_video', 'type': 'video',
                                'title': 'La Science des Habitudes',
                                'description': 'Comment fonctionne la boucle Signal-Routine-Recompense',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_1_3_pdf', 'type': 'pdf',
                                'title': 'Fiche Pratique - Tracker d\'Habitudes',
                                'description': 'Template pour suivre vos nouvelles habitudes au quotidien',
                                'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_1_3_qcm', 'type': 'qcm',
                                'title': 'QCM - Les Habitudes',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quels sont les 3 elements de la boucle des habitudes ?',
                                        'options': [
                                            'Motivation, Action, Resultat',
                                            'Signal, Routine, Recompense',
                                            'Objectif, Plan, Execution',
                                            'Desir, Effort, Satisfaction',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Combien de temps faut-il en moyenne pour installer une nouvelle habitude ?',
                                        'options': [
                                            '7 jours',
                                            '21 jours',
                                            '66 jours en moyenne',
                                            'Exactement 30 jours',
                                        ],
                                        'correct_index': 2,
                                    },
                                    {
                                        'question': 'Quelle strategie est la plus efficace pour changer une habitude ?',
                                        'options': [
                                            'Compter uniquement sur la volonte',
                                            'Remplacer la routine par une alternative positive en gardant le meme signal',
                                            'Eliminer toutes les habitudes d\'un coup',
                                            'Attendre d\'etre motive pour commencer',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'id': 'deg_lim_2',
                'title': 'Niveau 2: Productivite et Action',
                'description': 'Maitrisez votre temps et passez a l\'action avec efficacite',
                'order_index': 1,
                'files': [
                    {
                        'id': 'dfile_lim_2_1', 'type': 'pdf',
                        'title': 'Fiche Recap - Productivite',
                        'description': 'Resume des techniques de productivite du Niveau 2',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_lim_2_2', 'type': 'audio',
                        'title': 'Meditation Guidee - Focus',
                        'description': 'Meditation pour ameliorer votre concentration',
                        'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_lim_2_1',
                        'title': 'Gestion du Temps',
                        'description': 'Apprenez les techniques de gestion du temps les plus efficaces',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_lim_2_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Le temps est votre ressource la plus precieuse. '
                                    'Decouvrez la matrice d\'Eisenhower et la technique Pomodoro '
                                    'pour maximiser votre productivite.'
                                ),
                            },
                            {
                                'id': 'asset_lim_2_1_video', 'type': 'video',
                                'title': 'Maitriser la Gestion du Temps',
                                'description': 'Les techniques Pomodoro, Eisenhower et Time Blocking',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_2_1_pdf', 'type': 'pdf',
                                'title': 'Matrice d\'Eisenhower - Template',
                                'description': 'Template imprimable pour prioriser vos taches',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/versions/guidelines/wcag20-guidelines-20081211-a4.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_2_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Gestion du Temps',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Dans la matrice d\'Eisenhower, que faire des taches urgentes mais pas importantes ?',
                                        'options': [
                                            'Les faire immediatement soi-meme',
                                            'Les deleguer a quelqu\'un d\'autre',
                                            'Les planifier pour plus tard',
                                            'Les supprimer de la liste',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle est la duree standard d\'un cycle Pomodoro ?',
                                        'options': [
                                            '15 minutes de travail, 3 minutes de pause',
                                            '25 minutes de travail, 5 minutes de pause',
                                            '45 minutes de travail, 15 minutes de pause',
                                            '60 minutes de travail, 10 minutes de pause',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel est le principal ennemi de la productivite ?',
                                        'options': [
                                            'Le manque d\'outils',
                                            'Les interruptions et le multitache',
                                            'Le travail en equipe',
                                            'Les reunions planifiees',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_lim_2_2',
                        'title': 'Vaincre la Procrastination',
                        'description': 'Techniques pratiques pour passer a l\'action et arreter de reporter',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_lim_2_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'La procrastination n\'est pas de la paresse. '
                                    'C\'est souvent une reponse emotionnelle a la peur de l\'echec. '
                                    'Decouvrez les techniques pour la vaincre definitivement.'
                                ),
                            },
                            {
                                'id': 'asset_lim_2_2_video', 'type': 'video',
                                'title': 'Vaincre la Procrastination',
                                'description': 'La regle des 2 minutes et autres techniques anti-procrastination',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_2_2_audio', 'type': 'audio',
                                'title': 'Exercice de Visualisation - Passage a l\'Action',
                                'description': 'Audio guide de 10 minutes pour vous motiver a agir',
                                'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_2_2_form', 'type': 'form',
                                'title': 'Plan d\'Action Personnel',
                                'description': 'Definissez votre plan pour vaincre la procrastination',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_lim22_1', 'label': 'Quelle tache reportez-vous le plus souvent ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_lim22_2', 'label': 'Quelle emotion ressentez-vous avant de procrastiner ?', 'type': 'text', 'required': True},
                                    {'id': 'f_lim22_3', 'label': 'Quelle technique allez-vous appliquer cette semaine ?', 'type': 'textarea', 'required': True},
                                ],
                            },
                            {
                                'id': 'asset_lim_2_2_qcm', 'type': 'qcm',
                                'title': 'QCM - Procrastination',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Qu\'est-ce que la regle des 2 minutes ?',
                                        'options': [
                                            'Ne jamais travailler plus de 2 minutes',
                                            'Si une tache prend moins de 2 minutes, la faire immediatement',
                                            'Prendre 2 minutes de pause toutes les heures',
                                            'Mediter 2 minutes avant chaque tache',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle est la cause principale de la procrastination ?',
                                        'options': [
                                            'La paresse naturelle',
                                            'Le manque de temps',
                                            'Une reponse emotionnelle (peur, anxiete, inconfort)',
                                            'Le manque d\'intelligence',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_lim_2_3',
                        'title': 'Discipline Quotidienne',
                        'description': 'Construisez une routine matinale et une discipline de fer',
                        'order_index': 2,
                        'assets': [
                            {
                                'id': 'asset_lim_2_3_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'La discipline est le pont entre vos objectifs et vos resultats. '
                                    'Apprenez a construire une routine matinale puissante '
                                    'et a maintenir votre discipline au quotidien.'
                                ),
                            },
                            {
                                'id': 'asset_lim_2_3_video', 'type': 'video',
                                'title': 'Construire sa Routine Matinale',
                                'description': 'Les 5 piliers d\'une matinee productive',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_2_3_pdf', 'type': 'pdf',
                                'title': 'Template Routine Matinale',
                                'description': 'Planifiez votre routine matinale ideale',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_2_3_qcm', 'type': 'qcm',
                                'title': 'QCM - Discipline Quotidienne',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quel est le meilleur moment pour planifier sa journee ?',
                                        'options': [
                                            'Pendant la pause dejeuner',
                                            'La veille au soir ou tot le matin',
                                            'Quand on a du temps libre',
                                            'Le week-end pour toute la semaine',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Pourquoi la routine matinale est-elle importante ?',
                                        'options': [
                                            'Pour impressionner les autres',
                                            'Pour dormir moins longtemps',
                                            'Elle donne le ton de la journee et renforce la discipline',
                                            'Pour suivre une mode',
                                        ],
                                        'correct_index': 2,
                                    },
                                    {
                                        'question': 'Comment maintenir la discipline sur le long terme ?',
                                        'options': [
                                            'Se punir en cas d\'echec',
                                            'Commencer petit, etre regulier, et celebrer les progres',
                                            'Ne jamais prendre de pause',
                                            'Compter uniquement sur la motivation',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'id': 'deg_lim_3',
                'title': 'Niveau 3: Excellence et Vision',
                'description': "Definissez votre vision personnelle et visez l'excellence dans tout ce que vous faites",
                'order_index': 2,
                'files': [
                    {
                        'id': 'dfile_lim_3_1', 'type': 'pdf',
                        'title': 'Workbook - Vision Personnelle',
                        'description': 'Exercices pratiques pour definir votre vision',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_lim_3_2', 'type': 'video',
                        'title': 'Bonus - Interview Expert',
                        'description': 'Interview avec un expert en developpement personnel',
                        'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_lim_3_1',
                        'title': 'Definir sa Vision Personnelle',
                        'description': 'Construisez une vision claire et inspirante pour votre vie',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_lim_3_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Votre vision est votre boussole. Sans vision claire, '
                                    'vous risquez de vous eparpiller. Prenez le temps de '
                                    'definir ou vous voulez etre dans 5 et 10 ans.'
                                ),
                            },
                            {
                                'id': 'asset_lim_3_1_video', 'type': 'video',
                                'title': 'Comment Definir sa Vision de Vie',
                                'description': 'Les 7 domaines de vie a equilibrer pour une vision complete',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_3_1_pdf', 'type': 'pdf',
                                'title': 'Workbook - Ma Vision de Vie',
                                'description': 'Exercices guides pour definir votre vision personnelle',
                                'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_3_1_form', 'type': 'form',
                                'title': 'Ma Vision en 5 ans',
                                'description': 'Definissez votre vision personnelle',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_lim31_1', 'label': 'Ou vous voyez-vous dans 5 ans professionnellement ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_lim31_2', 'label': 'Quels sont vos 3 objectifs les plus importants ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_lim31_3', 'label': 'Quel impact voulez-vous avoir sur votre communaute ?', 'type': 'textarea', 'required': False},
                                ],
                            },
                            {
                                'id': 'asset_lim_3_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Vision Personnelle',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Pourquoi est-il important d\'avoir une vision claire ?',
                                        'options': [
                                            'Pour impressionner son entourage',
                                            'Elle sert de boussole et guide nos decisions quotidiennes',
                                            'Pour gagner plus d\'argent rapidement',
                                            'C\'est une obligation sociale',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quels domaines doit couvrir une vision de vie equilibree ?',
                                        'options': [
                                            'Uniquement la carriere et les finances',
                                            'Sante, relations, carriere, finances, developpement personnel, spiritualite, contribution',
                                            'Le travail et les loisirs uniquement',
                                            'Ce que les autres attendent de nous',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_lim_3_2',
                        'title': 'Excellence et Amelioration Continue',
                        'description': 'Adoptez la philosophie Kaizen pour une amelioration constante',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_lim_3_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'L\'excellence n\'est pas un acte, c\'est une habitude. '
                                    'Decouvrez la philosophie Kaizen (amelioration continue) '
                                    'et comment devenir 1% meilleur chaque jour.'
                                ),
                            },
                            {
                                'id': 'asset_lim_3_2_video', 'type': 'video',
                                'title': 'La Philosophie Kaizen',
                                'description': 'Comment devenir 1% meilleur chaque jour',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_lim_3_2_pdf', 'type': 'pdf',
                                'title': 'Guide Final - Plan d\'Excellence',
                                'description': 'Votre plan d\'action complet pour vivre dans l\'excellence',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/versions/guidelines/wcag20-guidelines-20081211-a4.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_lim_3_2_qcm', 'type': 'qcm',
                                'title': 'QCM Final - Excellence',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Que signifie le concept japonais Kaizen ?',
                                        'options': [
                                            'Changement radical et immediat',
                                            'Amelioration continue par petits pas',
                                            'Perfection absolue',
                                            'Competition avec les autres',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel est l\'effet de s\'ameliorer de 1% chaque jour pendant un an ?',
                                        'options': [
                                            'On est 3.65 fois meilleur (365%)',
                                            'On est 37 fois meilleur',
                                            'On est 12 fois meilleur',
                                            'Il n\'y a pas de difference significative',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Comment mesurer ses progres vers l\'excellence ?',
                                        'options': [
                                            'En se comparant aux autres uniquement',
                                            'En tenant un journal de progres et en mesurant ses KPIs personnels',
                                            'En attendant les compliments des autres',
                                            'En passant des examens chaque semaine',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },

    # ═══════════════ PROGRAMME PMS ═══════════════
    {
        'id': 'prog_pms',
        'name': 'Programme PMS',
        'description': (
            'Programme de Management Strategique pour les leaders d\'aujourd\'hui et de demain. '
            'Developpez vos competences en leadership, communication et gestion d\'equipe '
            'pour exceller dans votre environnement professionnel.'
        ),
        'image_url': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800',
        'price': 120000,
        'duration_weeks': 6,
        'presentation_video_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
        'degrees': [
            {
                'id': 'deg_pms_1',
                'title': 'Niveau 1: Leadership Fondamental',
                'description': 'Les bases du leadership personnel et de la communication efficace',
                'order_index': 0,
                'files': [
                    {
                        'id': 'dfile_pms_1_1', 'type': 'pdf',
                        'title': 'Guide du Leader - Niveau 1',
                        'description': 'Synthese des principes de leadership fondamental',
                        'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_pms_1_2', 'type': 'audio',
                        'title': 'Podcast - Styles de Leadership',
                        'description': 'Decouvrez les differents styles de leadership',
                        'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_pms_1_1',
                        'title': 'Decouverte du Leadership',
                        'description': 'Introduction aux differents styles de leadership et a leur impact',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_pms_1_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Le leadership n\'est pas un titre, c\'est un comportement. '
                                    'Dans cette etape, decouvrez les differents styles de leadership '
                                    'et identifiez le votre.'
                                ),
                            },
                            {
                                'id': 'asset_pms_1_1_video', 'type': 'video',
                                'title': 'Les Styles de Leadership',
                                'description': 'Directif, participatif, delegatif, transformationnel',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_pms_1_1_pdf', 'type': 'pdf',
                                'title': 'Guide des Styles de Leadership',
                                'description': 'Comparatif des differents styles et quand les utiliser',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_pms_1_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Leadership',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quel style de leadership implique de donner des directives claires et de superviser etroitement ?',
                                        'options': [
                                            'Leadership participatif',
                                            'Leadership delegatif',
                                            'Leadership directif',
                                            'Leadership transformationnel',
                                        ],
                                        'correct_index': 2,
                                    },
                                    {
                                        'question': 'Qu\'est-ce qui distingue un leader d\'un manager ?',
                                        'options': [
                                            'Le leader a toujours un titre superieur',
                                            'Le leader inspire et motive, le manager organise et controle',
                                            'Il n\'y a aucune difference',
                                            'Le manager est toujours meilleur que le leader',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel est le style de leadership le plus adapte pour une equipe experimentee et autonome ?',
                                        'options': [
                                            'Directif',
                                            'Autoritaire',
                                            'Delegatif',
                                            'Coercitif',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_pms_1_2',
                        'title': 'Communication Efficace',
                        'description': 'Maitrisez l\'art de la communication verbale et non-verbale',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_pms_1_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    '93% de la communication est non-verbale. '
                                    'Apprenez a ecouter activement, a formuler des feedbacks '
                                    'constructifs et a adapter votre communication.'
                                ),
                            },
                            {
                                'id': 'asset_pms_1_2_video', 'type': 'video',
                                'title': 'Les Cles de la Communication',
                                'description': 'Ecoute active, feedback constructif et communication assertive',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_pms_1_2_audio', 'type': 'audio',
                                'title': 'Exercice d\'Ecoute Active',
                                'description': 'Exercice pratique de 10 minutes pour ameliorer votre ecoute',
                                'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_pms_1_2_qcm', 'type': 'qcm',
                                'title': 'QCM - Communication',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Qu\'est-ce que l\'ecoute active ?',
                                        'options': [
                                            'Ecouter en faisant autre chose en meme temps',
                                            'Porter une attention totale a l\'interlocuteur et reformuler',
                                            'Attendre son tour pour parler',
                                            'Prendre des notes sans lever les yeux',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Comment formuler un feedback constructif ?',
                                        'options': [
                                            'Critiquer la personne directement',
                                            'Decrire le comportement observe, son impact, et proposer une alternative',
                                            'Eviter de donner du feedback pour ne pas blesser',
                                            'Attendre la reunion annuelle d\'evaluation',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel pourcentage de la communication est non-verbal ?',
                                        'options': [
                                            'Environ 10%',
                                            'Environ 30%',
                                            'Environ 55% (langage corporel) + 38% (ton) = 93%',
                                            'Environ 100%',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_pms_1_3',
                        'title': 'Intelligence Emotionnelle',
                        'description': 'Developpez votre intelligence emotionnelle pour mieux gerer vos relations',
                        'order_index': 2,
                        'assets': [
                            {
                                'id': 'asset_pms_1_3_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'L\'intelligence emotionnelle (QE) est plus importante que le QI '
                                    'pour reussir en tant que leader. Decouvrez les 5 composantes '
                                    'de l\'IE selon Daniel Goleman.'
                                ),
                            },
                            {
                                'id': 'asset_pms_1_3_video', 'type': 'video',
                                'title': 'L\'Intelligence Emotionnelle au Travail',
                                'description': 'Les 5 piliers : conscience de soi, maitrise de soi, motivation, empathie, competences sociales',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_pms_1_3_pdf', 'type': 'pdf',
                                'title': 'Auto-diagnostic Intelligence Emotionnelle',
                                'description': 'Evaluez votre QE actuel avec ce questionnaire',
                                'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_pms_1_3_form', 'type': 'form',
                                'title': 'Mon Profil Emotionnel',
                                'description': 'Evaluez vos competences emotionnelles',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_pms13_1', 'label': 'Dans quelle situation perdez-vous le plus souvent votre calme ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_pms13_2', 'label': 'Comment reagissez-vous face a un conflit ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_pms13_3', 'label': 'Quel aspect de votre IE souhaitez-vous ameliorer ?',
                                     'type': 'select', 'required': True,
                                     'select_options': ['Conscience de soi', 'Maitrise de soi', 'Motivation', 'Empathie', 'Competences sociales']},
                                ],
                            },
                            {
                                'id': 'asset_pms_1_3_qcm', 'type': 'qcm',
                                'title': 'QCM - Intelligence Emotionnelle',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Combien de composantes a l\'intelligence emotionnelle selon Goleman ?',
                                        'options': ['3', '5', '7', '10'],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Qu\'est-ce que l\'empathie dans le contexte du leadership ?',
                                        'options': [
                                            'Etre d\'accord avec tout le monde',
                                            'Comprendre et ressentir les emotions des autres pour mieux les accompagner',
                                            'Montrer ses propres emotions en public',
                                            'Eviter les conversations difficiles',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'id': 'deg_pms_2',
                'title': 'Niveau 2: Management Avance',
                'description': 'Techniques avancees de management et de gestion d\'equipe',
                'order_index': 1,
                'files': [
                    {
                        'id': 'dfile_pms_2_1', 'type': 'pdf',
                        'title': 'Guide du Manager',
                        'description': 'Les cles du management moderne',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_pms_2_2', 'type': 'audio',
                        'title': 'Podcast - Gestion d\'equipe',
                        'description': 'Techniques de gestion d\'equipe efficaces',
                        'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_pms_2_1',
                        'title': 'Strategie et Decision',
                        'description': 'Apprenez a prendre des decisions strategiques dans l\'incertitude',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_pms_2_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Un leader prend des decisions meme avec des informations incompletes. '
                                    'Decouvrez les frameworks de decision qui vous aideront '
                                    'a faire les bons choix strategiques.'
                                ),
                            },
                            {
                                'id': 'asset_pms_2_1_video', 'type': 'video',
                                'title': 'Prise de Decision Strategique',
                                'description': 'Frameworks SWOT, arbre de decision, analyse cout-benefice',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_pms_2_1_pdf', 'type': 'pdf',
                                'title': 'Template Analyse SWOT',
                                'description': 'Template pour realiser une analyse SWOT complete',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/versions/guidelines/wcag20-guidelines-20081211-a4.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_pms_2_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Decision Strategique',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Que signifie SWOT ?',
                                        'options': [
                                            'Strategy, Workforce, Operations, Technology',
                                            'Strengths, Weaknesses, Opportunities, Threats',
                                            'Sales, Web, Organization, Training',
                                            'Systems, Work, Objectives, Tasks',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle erreur courante faut-il eviter dans la prise de decision ?',
                                        'options': [
                                            'Consulter son equipe',
                                            'Analyser les donnees disponibles',
                                            'Le biais de confirmation (ne chercher que des preuves qui confirment notre idee)',
                                            'Prendre le temps de reflechir',
                                        ],
                                        'correct_index': 2,
                                    },
                                    {
                                        'question': 'Quand faut-il prendre une decision rapide ?',
                                        'options': [
                                            'Toujours, la vitesse est primordiale',
                                            'Quand le cout de l\'inaction depasse le risque d\'erreur',
                                            'Jamais, il faut toujours analyser longuement',
                                            'Uniquement quand le patron le demande',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_pms_2_2',
                        'title': 'Gestion d\'Equipe et Delegation',
                        'description': 'Apprenez a constituer, motiver et gerer une equipe performante',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_pms_2_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Un leader seul ne peut rien accomplir de grand. '
                                    'Apprenez a deleguer efficacement, a motiver votre equipe '
                                    'et a gerer les conflits de maniere constructive.'
                                ),
                            },
                            {
                                'id': 'asset_pms_2_2_video', 'type': 'video',
                                'title': 'L\'Art de la Delegation',
                                'description': 'Deleguer sans perdre le controle : methodes pratiques',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_pms_2_2_pdf', 'type': 'pdf',
                                'title': 'Guide de Delegation Efficace',
                                'description': 'Les 7 etapes d\'une delegation reussie',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_pms_2_2_form', 'type': 'form',
                                'title': 'Plan de Delegation',
                                'description': 'Planifiez vos prochaines delegations',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_pms22_1', 'label': 'Quelle tache allez-vous deleguer cette semaine ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_pms22_2', 'label': 'A qui allez-vous la deleguer et pourquoi ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_pms22_3', 'label': 'Comment allez-vous suivre l\'avancement ?', 'type': 'textarea', 'required': True},
                                ],
                            },
                            {
                                'id': 'asset_pms_2_2_qcm', 'type': 'qcm',
                                'title': 'QCM Final - Gestion d\'Equipe',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quelle est la premiere etape d\'une delegation efficace ?',
                                        'options': [
                                            'Donner la tache sans explication',
                                            'Definir clairement l\'objectif, le contexte et les attentes',
                                            'Surveiller chaque action du collaborateur',
                                            'Deleguer uniquement les taches ennuyeuses',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Comment motiver durablement une equipe ?',
                                        'options': [
                                            'Augmenter les salaires uniquement',
                                            'Donner de l\'autonomie, du sens et de la reconnaissance',
                                            'Mettre les membres en competition',
                                            'Eviter tout feedback negatif',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Que faire face a un conflit au sein de l\'equipe ?',
                                        'options': [
                                            'L\'ignorer, ca passera',
                                            'Prendre parti pour un des membres',
                                            'Ecouter les deux parties, identifier la cause et faciliter une resolution',
                                            'Sanctionner immediatement les deux parties',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },

    # ═══════════════ PROGRAMME BOOST ENTREPRENEUR ═══════════════
    {
        'id': 'prog_boost',
        'name': 'Programme Boost Entrepreneur',
        'description': (
            'Lancez votre entreprise avec les bonnes bases. '
            'De l\'idee au lancement, en passant par le business plan et le financement, '
            'ce programme vous guide pas a pas dans la creation de votre entreprise.'
        ),
        'image_url': 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800',
        'price': 200000,
        'duration_weeks': 10,
        'presentation_video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'degrees': [
            {
                'id': 'deg_boost_1',
                'title': 'Niveau 1: Idee et Validation',
                'description': 'Trouvez, evaluez et validez votre idee de business',
                'order_index': 0,
                'files': [
                    {
                        'id': 'dfile_boost_1_1', 'type': 'pdf',
                        'title': 'Template - Etude de Marche',
                        'description': 'Modele d\'etude de marche a remplir',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_boost_1_2', 'type': 'audio',
                        'title': 'Podcast - Trouver son Idee',
                        'description': 'Comment identifier une opportunite de business',
                        'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_boost_1_1',
                        'title': 'Trouver son Idee de Business',
                        'description': 'Methodes pour identifier des opportunites d\'affaires rentables',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_boost_1_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Chaque grande entreprise a commence par une idee. '
                                    'Mais une bonne idee de business resout un vrai probleme. '
                                    'Apprenez a identifier des opportunites autour de vous.'
                                ),
                            },
                            {
                                'id': 'asset_boost_1_1_video', 'type': 'video',
                                'title': 'Comment Trouver une Idee de Business',
                                'description': 'Les 5 methodes pour trouver une idee rentable en Afrique',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_boost_1_1_pdf', 'type': 'pdf',
                                'title': 'Workbook - Generateur d\'Idees',
                                'description': 'Exercices pour identifier 10 idees de business potentielles',
                                'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_boost_1_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Trouver son Idee',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quel est le meilleur point de depart pour trouver une idee de business ?',
                                        'options': [
                                            'Copier un business qui marche a l\'etranger',
                                            'Identifier un probleme reel que les gens sont prets a payer pour resoudre',
                                            'Choisir le secteur le plus a la mode',
                                            'Demander a ses amis ce qu\'ils veulent',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Qu\'est-ce qu\'un marche de niche ?',
                                        'options': [
                                            'Un marche avec beaucoup de concurrents',
                                            'Un segment specifique avec des besoins particuliers et peu concurrence',
                                            'Un marche impossible a atteindre',
                                            'Un marche reserve aux grandes entreprises',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel critere est le plus important pour evaluer une idee de business ?',
                                        'options': [
                                            'Que l\'idee soit originale et jamais vue',
                                            'Qu\'elle necessite peu d\'investissement',
                                            'Qu\'il existe une demande reelle et solvable',
                                            'Qu\'elle soit facile a realiser seul',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_boost_1_2',
                        'title': 'Etude de Marche',
                        'description': 'Realisez une etude de marche simple mais efficace',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_boost_1_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Avant d\'investir du temps et de l\'argent, validez votre marche. '
                                    'Une etude de marche ne doit pas etre compliquee : '
                                    'allez parler a vos futurs clients !'
                                ),
                            },
                            {
                                'id': 'asset_boost_1_2_video', 'type': 'video',
                                'title': 'Realiser son Etude de Marche',
                                'description': 'Methodes terrain et en ligne pour valider votre marche',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_boost_1_2_pdf', 'type': 'pdf',
                                'title': 'Template Questionnaire Client',
                                'description': 'Questionnaire pret a l\'emploi pour interviewer vos futurs clients',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/versions/guidelines/wcag20-guidelines-20081211-a4.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_boost_1_2_form', 'type': 'form',
                                'title': 'Resultats de votre Etude de Marche',
                                'description': 'Resumez vos decouvertes',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_boost12_1', 'label': 'Combien de personnes avez-vous interrogees ?', 'type': 'text', 'required': True},
                                    {'id': 'f_boost12_2', 'label': 'Quel probleme principal avez-vous identifie ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_boost12_3', 'label': 'Combien seraient prets a payer pour votre solution ?', 'type': 'text', 'required': True},
                                ],
                            },
                            {
                                'id': 'asset_boost_1_2_qcm', 'type': 'qcm',
                                'title': 'QCM - Etude de Marche',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quelle est la methode la plus fiable pour une etude de marche ?',
                                        'options': [
                                            'Lire des articles sur internet',
                                            'Aller sur le terrain et parler directement aux clients potentiels',
                                            'Demander l\'avis de sa famille',
                                            'Faire un sondage sur les reseaux sociaux uniquement',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Que doit-on mesurer en priorite dans une etude de marche ?',
                                        'options': [
                                            'Le nombre de concurrents uniquement',
                                            'La taille du marche, la demande reelle et la disposition a payer',
                                            'Les tendances sur les reseaux sociaux',
                                            'Le chiffre d\'affaires des concurrents',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'id': 'deg_boost_2',
                'title': 'Niveau 2: Business Plan et Financement',
                'description': 'Construisez votre plan d\'affaires et trouvez des financements',
                'order_index': 1,
                'files': [
                    {
                        'id': 'dfile_boost_2_1', 'type': 'pdf',
                        'title': 'Template - Business Plan',
                        'description': 'Modele de business plan professionnel',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_boost_2_1',
                        'title': 'Rediger son Business Plan',
                        'description': 'Les composantes essentielles d\'un business plan convaincant',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_boost_2_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Le business plan est votre feuille de route et votre outil '
                                    'de persuasion aupres des investisseurs. Apprenez a en rediger '
                                    'un qui soit clair, realiste et convaincant.'
                                ),
                            },
                            {
                                'id': 'asset_boost_2_1_video', 'type': 'video',
                                'title': 'Rediger un Business Plan Gagnant',
                                'description': 'Les 9 sections essentielles d\'un business plan',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_boost_2_1_pdf', 'type': 'pdf',
                                'title': 'Template Business Plan',
                                'description': 'Modele complet de business plan a remplir',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_boost_2_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Business Plan',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quelle section du business plan est lue en premier par un investisseur ?',
                                        'options': [
                                            'L\'analyse financiere',
                                            'Le resume executif (executive summary)',
                                            'L\'etude de marche',
                                            'L\'equipe fondatrice',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel element est indispensable dans un business plan ?',
                                        'options': [
                                            'Une description detaillee de la technologie utilisee',
                                            'Les previsions financieres sur 3 a 5 ans',
                                            'Le CV complet de chaque employe',
                                            'La liste des fournisseurs avec leurs prix',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Qu\'est-ce qu\'une proposition de valeur ?',
                                        'options': [
                                            'Le prix de vente du produit',
                                            'La promesse unique qui explique pourquoi un client devrait vous choisir',
                                            'Le montant d\'investissement necessaire',
                                            'La valeur boursiere de l\'entreprise',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_boost_2_2',
                        'title': 'Previsions Financieres',
                        'description': 'Maitrisez les bases de la prevision financiere pour entrepreneurs',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_boost_2_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Les chiffres ne mentent pas. Apprenez a construire des previsions '
                                    'financieres realistes : compte de resultat, tresorerie et seuil '
                                    'de rentabilite.'
                                ),
                            },
                            {
                                'id': 'asset_boost_2_2_video', 'type': 'video',
                                'title': 'Previsions Financieres pour Debutants',
                                'description': 'Compte de resultat, tresorerie et point mort expliques simplement',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_boost_2_2_pdf', 'type': 'pdf',
                                'title': 'Template Previsions Financieres',
                                'description': 'Tableur Excel/PDF pour vos previsions sur 3 ans',
                                'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_boost_2_2_form', 'type': 'form',
                                'title': 'Vos Chiffres Cles',
                                'description': 'Estimez les chiffres cles de votre projet',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_boost22_1', 'label': 'Quel est votre investissement initial estime (FCFA) ?', 'type': 'text', 'required': True},
                                    {'id': 'f_boost22_2', 'label': 'Quel chiffre d\'affaires visez-vous la premiere annee ?', 'type': 'text', 'required': True},
                                    {'id': 'f_boost22_3', 'label': 'Quelles sont vos charges fixes mensuelles estimees ?', 'type': 'text', 'required': True},
                                ],
                            },
                            {
                                'id': 'asset_boost_2_2_qcm', 'type': 'qcm',
                                'title': 'QCM - Previsions Financieres',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Qu\'est-ce que le seuil de rentabilite (point mort) ?',
                                        'options': [
                                            'Le montant maximum de ventes possible',
                                            'Le chiffre d\'affaires minimum pour couvrir toutes les charges',
                                            'Le benefice net de l\'entreprise',
                                            'Le montant des investissements necessaires',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle est la difference entre charges fixes et charges variables ?',
                                        'options': [
                                            'Il n\'y a pas de difference',
                                            'Les charges fixes ne changent pas selon l\'activite, les variables oui',
                                            'Les charges fixes sont plus elevees',
                                            'Les charges variables sont payees une seule fois',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Pourquoi le plan de tresorerie est-il crucial ?',
                                        'options': [
                                            'Pour payer moins d\'impots',
                                            'Pour anticiper les periodes ou l\'entreprise manquera de liquidites',
                                            'Pour impressionner les investisseurs uniquement',
                                            'Ce n\'est pas vraiment important au debut',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'id': 'deg_boost_3',
                'title': 'Niveau 3: Lancement et Croissance',
                'description': 'Lancez votre entreprise et developpez vos premieres ventes',
                'order_index': 2,
                'files': [
                    {
                        'id': 'dfile_boost_3_1', 'type': 'pdf',
                        'title': 'Checklist - Lancement Produit',
                        'description': 'Liste de verification avant le lancement',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_boost_3_2', 'type': 'audio',
                        'title': 'Podcast - Marketing Digital',
                        'description': 'Strategies de marketing pour startups',
                        'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_boost_3_1',
                        'title': 'Marketing et Premieres Ventes',
                        'description': 'Strategies marketing accessibles pour lancer vos ventes',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_boost_3_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Le meilleur produit du monde ne se vend pas tout seul. '
                                    'Decouvrez les strategies marketing efficaces et accessibles '
                                    'pour vos premieres ventes.'
                                ),
                            },
                            {
                                'id': 'asset_boost_3_1_video', 'type': 'video',
                                'title': 'Marketing Digital pour Entrepreneurs',
                                'description': 'Reseaux sociaux, WhatsApp Business et marketing de contenu',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_boost_3_1_pdf', 'type': 'pdf',
                                'title': 'Plan Marketing en 1 Page',
                                'description': 'Template pour definir votre strategie marketing',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/versions/guidelines/wcag20-guidelines-20081211-a4.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_boost_3_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Marketing',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quel est le canal marketing le plus efficace en Afrique de l\'Ouest ?',
                                        'options': [
                                            'Les publicites TV uniquement',
                                            'Les reseaux sociaux et WhatsApp Business',
                                            'Les panneaux publicitaires',
                                            'Le marketing par email uniquement',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Qu\'est-ce que le marketing de contenu ?',
                                        'options': [
                                            'Publier des publicites en permanence',
                                            'Creer du contenu utile et gratuit pour attirer et fideliser des clients',
                                            'Copier le contenu des concurrents',
                                            'Envoyer des messages non sollicites',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_boost_3_2',
                        'title': 'Lancement et Croissance',
                        'description': 'Les etapes cles pour lancer officiellement et faire croitre votre business',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_boost_3_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Felicitations, vous etes pret a lancer ! '
                                    'Decouvrez les etapes cles du lancement et les strategies '
                                    'de croissance pour les 6 premiers mois.'
                                ),
                            },
                            {
                                'id': 'asset_boost_3_2_video', 'type': 'video',
                                'title': 'Reussir son Lancement',
                                'description': 'Checklist de lancement et strategies de croissance initiale',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_boost_3_2_audio', 'type': 'audio',
                                'title': 'Temoignage - Un Entrepreneur Partage son Experience',
                                'description': 'Retour d\'experience d\'un entrepreneur ivoirien qui a reussi',
                                'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_boost_3_2_form', 'type': 'form',
                                'title': 'Mon Plan de Lancement',
                                'description': 'Definissez votre plan de lancement',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_boost32_1', 'label': 'Quelle est votre date de lancement prevue ?', 'type': 'text', 'required': True},
                                    {'id': 'f_boost32_2', 'label': 'Quel est votre objectif de ventes pour le premier mois ?', 'type': 'text', 'required': True},
                                    {'id': 'f_boost32_3', 'label': 'Quels sont les 3 actions marketing de votre premiere semaine ?', 'type': 'textarea', 'required': True},
                                ],
                            },
                            {
                                'id': 'asset_boost_3_2_qcm', 'type': 'qcm',
                                'title': 'QCM Final - Lancement',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quel est le concept du MVP (Minimum Viable Product) ?',
                                        'options': [
                                            'Un produit parfait avant le lancement',
                                            'La version la plus simple de votre produit qui resout le probleme principal',
                                            'Un prototype qui ne fonctionne pas',
                                            'Un produit gratuit pour les premiers clients',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle strategie de croissance est la plus durable ?',
                                        'options': [
                                            'Baisser ses prix constamment',
                                            'Investir massivement en publicite',
                                            'Le bouche-a-oreille grace a un excellent service client',
                                            'Copier les strategies des grands groupes',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },

    # ═══════════════ PROGRAMME FINANCE PERSONNELLE ═══════════════
    {
        'id': 'prog_finance',
        'name': 'Programme Finance Personnelle',
        'description': (
            'Maitrisez vos finances personnelles et investissez intelligemment. '
            'Apprenez a budgetiser, epargner et faire fructifier votre argent '
            'pour atteindre la liberte financiere.'
        ),
        'image_url': 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800',
        'price': 100000,
        'duration_weeks': 4,
        'presentation_video_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
        'degrees': [
            {
                'id': 'deg_fin_1',
                'title': 'Niveau 1: Budget et Epargne',
                'description': 'Les fondamentaux de la gestion financiere personnelle',
                'order_index': 0,
                'files': [
                    {
                        'id': 'dfile_fin_1_1', 'type': 'pdf',
                        'title': 'Template - Budget Mensuel',
                        'description': 'Tableau de budget mensuel a telecharger',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                    {
                        'id': 'dfile_fin_1_2', 'type': 'audio',
                        'title': 'Podcast - Habitudes d\'Epargne',
                        'description': 'Comment epargner efficacement chaque mois',
                        'external_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3',
                        'order_index': 1,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_fin_1_1',
                        'title': 'Creer son Budget',
                        'description': 'Apprenez a etablir un budget mensuel realiste et efficace',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_fin_1_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Un budget n\'est pas une restriction, c\'est un plan pour votre argent. '
                                    'La regle 50/30/20 est un excellent point de depart : '
                                    '50% besoins, 30% envies, 20% epargne.'
                                ),
                            },
                            {
                                'id': 'asset_fin_1_1_video', 'type': 'video',
                                'title': 'Comment Creer un Budget Efficace',
                                'description': 'La methode 50/30/20 et les outils de budgetisation',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_fin_1_1_pdf', 'type': 'pdf',
                                'title': 'Template Budget Mensuel',
                                'description': 'Tableau budget a remplir pour le mois en cours',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_fin_1_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Budget',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Dans la regle 50/30/20, a quoi correspondent les 20% ?',
                                        'options': [
                                            'Les depenses de loisirs',
                                            'Les besoins essentiels',
                                            'L\'epargne et le remboursement de dettes',
                                            'Les depenses imprevues',
                                        ],
                                        'correct_index': 2,
                                    },
                                    {
                                        'question': 'Quelle est la premiere etape pour creer un budget ?',
                                        'options': [
                                            'Ouvrir un compte d\'epargne',
                                            'Lister toutes ses sources de revenus et ses depenses',
                                            'Couper toutes les depenses non essentielles',
                                            'Investir en bourse',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Pourquoi faut-il revoir son budget regulierement ?',
                                        'options': [
                                            'Ce n\'est pas necessaire si le budget est bien fait',
                                            'Parce que les revenus et depenses changent avec le temps',
                                            'Uniquement si on gagne plus d\'argent',
                                            'Seulement une fois par an suffit',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_fin_1_2',
                        'title': 'Strategies d\'Epargne',
                        'description': 'Decouvrez les meilleures strategies pour epargner efficacement',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_fin_1_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Epargner n\'est pas ce qu\'il reste a la fin du mois, '
                                    'c\'est ce qu\'on met de cote en premier. '
                                    'Decouvrez la strategie "Payez-vous en premier".'
                                ),
                            },
                            {
                                'id': 'asset_fin_1_2_video', 'type': 'video',
                                'title': 'Les Secrets de l\'Epargne',
                                'description': 'Payez-vous en premier et automatisez votre epargne',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_fin_1_2_pdf', 'type': 'pdf',
                                'title': 'Plan d\'Epargne sur 12 Mois',
                                'description': 'Template pour planifier votre epargne sur une annee',
                                'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_fin_1_2_form', 'type': 'form',
                                'title': 'Mon Objectif d\'Epargne',
                                'description': 'Definissez votre objectif d\'epargne',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_fin12_1', 'label': 'Quel montant souhaitez-vous epargner par mois (FCFA) ?', 'type': 'text', 'required': True},
                                    {'id': 'f_fin12_2', 'label': 'Pour quel objectif epargnez-vous ?', 'type': 'textarea', 'required': True},
                                    {'id': 'f_fin12_3', 'label': 'Quel pourcentage de vos revenus cela represente-t-il ?', 'type': 'text', 'required': False},
                                ],
                            },
                            {
                                'id': 'asset_fin_1_2_qcm', 'type': 'qcm',
                                'title': 'QCM - Epargne',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Que signifie "Payez-vous en premier" ?',
                                        'options': [
                                            'Se faire plaisir avant de payer ses factures',
                                            'Mettre de cote son epargne des reception du salaire, avant les depenses',
                                            'Ne pas payer ses dettes',
                                            'Depenser pour soi avant les autres',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Qu\'est-ce qu\'un fonds d\'urgence ?',
                                        'options': [
                                            'Un investissement a haut rendement',
                                            'Une reserve de 3 a 6 mois de depenses pour les imprevus',
                                            'Un credit pour les urgences',
                                            'Un compte pour les vacances',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle est la meilleure strategie pour epargner regulierement ?',
                                        'options': [
                                            'Attendre d\'avoir un surplus en fin de mois',
                                            'Automatiser un virement vers son compte d\'epargne chaque mois',
                                            'Epargner uniquement quand on a une grosse rentree',
                                            'Garder l\'argent sous le matelas',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_fin_1_3',
                        'title': 'Eliminer les Dettes',
                        'description': 'Strategies pour se liberer de l\'endettement',
                        'order_index': 2,
                        'assets': [
                            {
                                'id': 'asset_fin_1_3_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Les dettes sont le plus grand frein a la liberte financiere. '
                                    'Decouvrez les methodes Avalanche et Boule de Neige '
                                    'pour vous liberer de vos dettes systematiquement.'
                                ),
                            },
                            {
                                'id': 'asset_fin_1_3_video', 'type': 'video',
                                'title': 'Se Liberer des Dettes',
                                'description': 'Methodes Avalanche vs Boule de Neige pour eliminer ses dettes',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_fin_1_3_pdf', 'type': 'pdf',
                                'title': 'Tableau de Suivi des Dettes',
                                'description': 'Template pour lister et suivre le remboursement de vos dettes',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/versions/guidelines/wcag20-guidelines-20081211-a4.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_fin_1_3_qcm', 'type': 'qcm',
                                'title': 'QCM - Gestion des Dettes',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quelle est la methode "Boule de Neige" pour rembourser ses dettes ?',
                                        'options': [
                                            'Rembourser la dette avec le taux d\'interet le plus eleve en premier',
                                            'Rembourser la plus petite dette en premier pour creer de la motivation',
                                            'Payer le minimum sur toutes les dettes',
                                            'Contracter un nouveau pret pour rembourser les anciens',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quelle est la difference avec la methode "Avalanche" ?',
                                        'options': [
                                            'Il n\'y a pas de difference',
                                            'L\'Avalanche rembourse la dette au taux d\'interet le plus eleve en premier',
                                            'L\'Avalanche ignore les petites dettes',
                                            'L\'Avalanche est illegale',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'id': 'deg_fin_2',
                'title': 'Niveau 2: Investissement',
                'description': 'Introduction a l\'investissement et a la creation de richesse',
                'order_index': 1,
                'files': [
                    {
                        'id': 'dfile_fin_2_1', 'type': 'pdf',
                        'title': 'Guide - Premiers Investissements',
                        'description': 'Guide pratique pour debuter en investissement',
                        'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                        'order_index': 0,
                    },
                ],
                'steps': [
                    {
                        'id': 'step_fin_2_1',
                        'title': 'Introduction a l\'Investissement',
                        'description': 'Les bases de l\'investissement pour les debutants',
                        'order_index': 0,
                        'assets': [
                            {
                                'id': 'asset_fin_2_1_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Investir c\'est faire travailler votre argent pour vous. '
                                    'Decouvrez les differents types d\'investissement accessibles '
                                    'en Afrique de l\'Ouest et leurs niveaux de risque.'
                                ),
                            },
                            {
                                'id': 'asset_fin_2_1_video', 'type': 'video',
                                'title': 'Les Bases de l\'Investissement',
                                'description': 'Actions, obligations, immobilier, tontines : comprendre les options',
                                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_fin_2_1_pdf', 'type': 'pdf',
                                'title': 'Guide de l\'Investisseur Debutant',
                                'description': 'Comparatif des options d\'investissement en Afrique de l\'Ouest',
                                'external_url': 'https://www.w3.org/WAI/WCAG20/glance/WCAG2-at-a-Glance.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_fin_2_1_qcm', 'type': 'qcm',
                                'title': 'QCM - Investissement',
                                'order_index': 3, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Quel est le principe fondamental de l\'investissement ?',
                                        'options': [
                                            'Investir tout son argent dans un seul actif',
                                            'Plus le rendement potentiel est eleve, plus le risque est important',
                                            'L\'investissement est toujours sans risque',
                                            'Il faut investir uniquement dans ce qu\'on connait personnellement',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Qu\'est-ce que la diversification ?',
                                        'options': [
                                            'Investir tout dans le meme secteur',
                                            'Repartir ses investissements sur differents actifs pour reduire le risque',
                                            'Changer d\'investissement chaque mois',
                                            'Investir uniquement dans l\'immobilier',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel investissement est generalement considere comme le moins risque ?',
                                        'options': [
                                            'Les actions individuelles',
                                            'Les crypto-monnaies',
                                            'Les obligations d\'Etat et les comptes d\'epargne',
                                            'Les startups',
                                        ],
                                        'correct_index': 2,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'id': 'step_fin_2_2',
                        'title': 'Premiers Investissements Pratiques',
                        'description': 'Passez a l\'action avec vos premiers investissements',
                        'order_index': 1,
                        'assets': [
                            {
                                'id': 'asset_fin_2_2_consigne', 'type': 'consigne',
                                'title': "Consignes de l'etape", 'order_index': 0,
                                'consigne_text': (
                                    'Il est temps de passer a l\'action ! '
                                    'Decouvrez comment ouvrir un compte d\'investissement, '
                                    'comment commencer avec de petits montants et les pieges a eviter.'
                                ),
                            },
                            {
                                'id': 'asset_fin_2_2_video', 'type': 'video',
                                'title': 'Mes Premiers Investissements',
                                'description': 'Guide pratique pour commencer a investir avec peu de moyens',
                                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                'order_index': 1,
                            },
                            {
                                'id': 'asset_fin_2_2_pdf', 'type': 'pdf',
                                'title': 'Plan d\'Investissement Personnel',
                                'description': 'Votre feuille de route pour les 12 prochains mois',
                                'external_url': 'https://ia601209.us.archive.org/21/items/ERIC_ED460188/ERIC_ED460188.pdf',
                                'order_index': 2,
                            },
                            {
                                'id': 'asset_fin_2_2_form', 'type': 'form',
                                'title': 'Mon Premier Plan d\'Investissement',
                                'description': 'Definissez votre strategie d\'investissement',
                                'order_index': 3,
                                'form_fields': [
                                    {'id': 'f_fin22_1', 'label': 'Quel montant pouvez-vous investir chaque mois (FCFA) ?', 'type': 'text', 'required': True},
                                    {'id': 'f_fin22_2', 'label': 'Quel est votre horizon d\'investissement ?',
                                     'type': 'select', 'required': True,
                                     'select_options': ['Court terme (< 1 an)', 'Moyen terme (1-5 ans)', 'Long terme (> 5 ans)']},
                                    {'id': 'f_fin22_3', 'label': 'Quel type d\'investissement vous interesse le plus ?', 'type': 'textarea', 'required': True},
                                ],
                            },
                            {
                                'id': 'asset_fin_2_2_qcm', 'type': 'qcm',
                                'title': 'QCM Final - Investissement Pratique',
                                'order_index': 4, 'passing_score': 70,
                                'questions': [
                                    {
                                        'question': 'Avec combien peut-on commencer a investir ?',
                                        'options': [
                                            'Il faut au moins 1 million FCFA',
                                            'On peut commencer avec de petits montants (5000-10000 FCFA/mois)',
                                            'Il faut attendre d\'etre riche pour investir',
                                            'Minimum 500 000 FCFA',
                                        ],
                                        'correct_index': 1,
                                    },
                                    {
                                        'question': 'Quel est le piege le plus courant pour les investisseurs debutants ?',
                                        'options': [
                                            'Diversifier ses investissements',
                                            'Investir regulierement de petites sommes',
                                            'Chercher des rendements tres eleves rapidement (arnaques)',
                                            'Lire des livres sur l\'investissement',
                                        ],
                                        'correct_index': 2,
                                    },
                                    {
                                        'question': 'Qu\'est-ce que l\'interet compose ?',
                                        'options': [
                                            'Un interet qui diminue avec le temps',
                                            'Les interets qui generent eux-memes des interets, accelerant la croissance',
                                            'Un taux d\'interet fixe pour les prets',
                                            'Un interet paye uniquement a la fin du placement',
                                        ],
                                        'correct_index': 1,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with complete test data for all programs'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        self._create_users()
        self._create_all_programs()
        self._create_enrollments()
        self._create_progress()
        self._create_sessions()
        self._create_testimonies()
        self._create_faq()
        self._create_contact()

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    # ────────────────────── USERS ──────────────────────

    def _create_users(self):
        self.stdout.write('  Creating users...')

        users_data = [
            {'id': 'usr_test_001', 'first_name': 'Jean', 'last_name': 'Dupont',
             'phone': '+22507000000', 'email': 'jean.dupont@example.com',
             'date_of_birth': '1990-05-15', 'city': 'Abidjan', 'country': "Cote d'Ivoire"},
            {'id': 'user_2', 'first_name': 'Marie', 'last_name': 'Kouassi',
             'phone': '+22507000001', 'city': 'Abidjan', 'country': "Cote d'Ivoire"},
            {'id': 'user_3', 'first_name': 'Amadou', 'last_name': 'Diallo',
             'phone': '+22507000002', 'city': 'Abidjan', 'country': "Cote d'Ivoire"},
            {'id': 'user_4', 'first_name': 'Fatou', 'last_name': 'Bamba',
             'phone': '+22507000003', 'city': 'Yamoussoukro', 'country': "Cote d'Ivoire"},
            {'id': 'user_5', 'first_name': 'Kouame', 'last_name': 'Assi',
             'phone': '+22507000004', 'city': 'Bouake', 'country': "Cote d'Ivoire"},
        ]

        self.users = []
        for u in users_data:
            uid = u.pop('id')
            user, _ = User.objects.update_or_create(id=uid, defaults=u)
            user.set_password('Test1234')
            user.save()
            self.users.append(user)

        self.user1, self.user2, self.user3, self.user4, self.user5 = self.users

    # ────────────────────── PROGRAMS (data-driven) ──────────────────────

    def _create_all_programs(self):
        self.stdout.write('  Creating programs, degrees, steps, assets...')

        self.programs = {}

        for prog_data in PROGRAMS_DATA:
            degrees_data = prog_data.pop('degrees')
            prog, _ = Program.objects.update_or_create(
                id=prog_data['id'],
                defaults={k: v for k, v in prog_data.items() if k != 'id'},
            )
            self.programs[prog_data['id']] = prog

            for deg_data in degrees_data:
                steps_data = deg_data.pop('steps')
                files_data = deg_data.pop('files', [])
                deg, _ = Degree.objects.update_or_create(
                    id=deg_data['id'],
                    defaults={
                        'program': prog,
                        'title': deg_data['title'],
                        'description': deg_data['description'],
                        'order_index': deg_data['order_index'],
                    },
                )

                # Create degree-level files
                DegreeFile.objects.filter(degree=deg).delete()
                for file_data in files_data:
                    DegreeFile.objects.create(
                        id=file_data['id'],
                        degree=deg,
                        type=file_data['type'],
                        title=file_data['title'],
                        description=file_data.get('description', ''),
                        external_url=file_data.get('external_url'),
                        order_index=file_data['order_index'],
                    )

                for step_data in steps_data:
                    assets_data = step_data.pop('assets')
                    step, _ = Step.objects.update_or_create(
                        id=step_data['id'],
                        defaults={
                            'degree': deg,
                            'title': step_data['title'],
                            'description': step_data['description'],
                            'order_index': step_data['order_index'],
                        },
                    )

                    # Delete ALL old assets for this step to avoid unique
                    # constraint conflicts when order_indexes have changed
                    Asset.objects.filter(step=step).delete()

                    for asset_data in assets_data:
                        self._create_asset(step, asset_data)

        # Restore the degrees back to avoid issues on re-run
        for prog_data in PROGRAMS_DATA:
            if 'degrees' not in prog_data:
                # Data was popped, but since this is module-level constant
                # it should only be an issue if seed is called twice in same process.
                pass

    def _create_asset(self, step, asset_data):
        """Create a single asset with its related objects (QCM questions, form fields)."""
        questions_data = asset_data.pop('questions', None)
        form_fields_data = asset_data.pop('form_fields', None)

        asset_id = asset_data.pop('id')
        asset_type = asset_data.pop('type')

        defaults = {
            'step': step,
            'type': asset_type,
            'title': asset_data.get('title', ''),
            'order_index': asset_data.get('order_index', 0),
        }
        if asset_data.get('description'):
            defaults['description'] = asset_data['description']
        if asset_data.get('external_url'):
            defaults['external_url'] = asset_data['external_url']
        if asset_data.get('consigne_text'):
            defaults['consigne_text'] = asset_data['consigne_text']
        if asset_data.get('passing_score'):
            defaults['passing_score'] = asset_data['passing_score']

        asset, _ = Asset.objects.update_or_create(id=asset_id, defaults=defaults)

        if questions_data:
            # Delete old questions and recreate for clean update
            QCMQuestion.objects.filter(asset=asset).delete()
            for i, q in enumerate(questions_data):
                QCMQuestion.objects.create(
                    asset=asset,
                    order_index=i,
                    question=q['question'],
                    options=q['options'],
                    correct_index=q['correct_index'],
                )

        if form_fields_data:
            # Delete old fields and recreate for clean update
            FormFieldDef.objects.filter(asset=asset).delete()
            for i, f in enumerate(form_fields_data):
                defaults_ff = {
                    'asset': asset,
                    'label': f['label'],
                    'type': f['type'],
                    'required': f.get('required', False),
                    'order_index': i,
                }
                if f.get('select_options'):
                    defaults_ff['select_options'] = f['select_options']
                FormFieldDef.objects.update_or_create(id=f['id'], defaults=defaults_ff)

    # ────────────────────── ENROLLMENTS ──────────────────────

    def _create_enrollments(self):
        self.stdout.write('  Creating enrollments...')

        prog_limitless = self.programs['prog_limitless']
        prog_pms = self.programs['prog_pms']

        self.enr1, _ = Enrollment.objects.update_or_create(
            id='enr_001',
            defaults={
                'program': prog_limitless,
                'user': self.user1,
                'payment_type': 'full',
                'payment_status': 'completed',
                'amount_paid': 150000,
                'total_amount': 150000,
            }
        )

        Payment.objects.update_or_create(
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

        self.enr2, _ = Enrollment.objects.update_or_create(
            id='enr_002',
            defaults={
                'program': prog_pms,
                'user': self.user1,
                'payment_type': 'installment',
                'payment_status': 'partial',
                'amount_paid': 60000,
                'total_amount': 120000,
            }
        )

        Payment.objects.update_or_create(
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

    # ────────────────────── PROGRESS ──────────────────────

    def _create_progress(self):
        self.stdout.write('  Creating progress...')

        prog_limitless = self.programs['prog_limitless']
        prog_pms = self.programs['prog_pms']

        # Limitless: step 1.1 completed, step 1.2 available, rest locked
        limitless_steps = [
            ('step_lim_1_1', 'completed'),
            ('step_lim_1_2', 'available'),
            ('step_lim_1_3', 'locked'),
            ('step_lim_2_1', 'locked'),
            ('step_lim_2_2', 'locked'),
            ('step_lim_2_3', 'locked'),
            ('step_lim_3_1', 'locked'),
            ('step_lim_3_2', 'locked'),
        ]

        for step_id, status in limitless_steps:
            try:
                step = Step.objects.get(id=step_id)
                StepProgress.objects.update_or_create(
                    user=self.user1, step=step,
                    defaults={'program': prog_limitless, 'status': status},
                )
            except Step.DoesNotExist:
                pass

        # Mark all assets in step_lim_1_1 as completed
        for asset in Asset.objects.filter(step_id='step_lim_1_1'):
            if asset.type in ('pdf', 'audio', 'video'):
                AssetCompletion.objects.get_or_create(
                    user=self.user1, asset=asset,
                    defaults={'program': prog_limitless},
                )
            elif asset.type == 'qcm':
                QCMAttempt.objects.get_or_create(
                    user=self.user1, asset=asset,
                    defaults={
                        'score': 100.0, 'passed': True,
                        'answers': [
                            {'questionIndex': 0, 'selectedOptionIndex': 1},
                            {'questionIndex': 1, 'selectedOptionIndex': 2},
                            {'questionIndex': 2, 'selectedOptionIndex': 2},
                        ],
                    }
                )
                AssetCompletion.objects.get_or_create(
                    user=self.user1, asset=asset,
                    defaults={'program': prog_limitless},
                )

        try:
            ConsigneAcceptance.objects.get_or_create(
                user=self.user1, step=Step.objects.get(id='step_lim_1_1'),
            )
        except Step.DoesNotExist:
            pass

        # PMS: step_pms_1_1 available, rest locked
        pms_steps = [
            ('step_pms_1_1', 'available'),
            ('step_pms_1_2', 'locked'),
            ('step_pms_1_3', 'locked'),
            ('step_pms_2_1', 'locked'),
            ('step_pms_2_2', 'locked'),
        ]
        for step_id, status in pms_steps:
            try:
                step = Step.objects.get(id=step_id)
                StepProgress.objects.update_or_create(
                    user=self.user1, step=step,
                    defaults={'program': prog_pms, 'status': status},
                )
            except Step.DoesNotExist:
                pass

    # ────────────────────── SESSIONS ──────────────────────

    def _create_sessions(self):
        self.stdout.write('  Creating sessions...')

        now = timezone.now()

        sessions = [
            {
                'id': 'live_1', 'title': 'Live - Revision Mindset',
                'description': 'Session de revision interactive sur les principes du mindset de croissance',
                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'date': now + timedelta(days=2), 'duration_minutes': 90, 'is_live': True,
            },
            {
                'id': 'live_2', 'title': 'Live - Atelier Leadership',
                'description': 'Atelier pratique sur le leadership au quotidien',
                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                'date': now + timedelta(days=9), 'duration_minutes': 120, 'is_live': True,
            },
            {
                'id': 'replay_1', 'title': 'Replay - Mindset de Croissance',
                'description': 'Revisionnez la session complete sur le mindset de croissance',
                'external_url': 'https://www.youtube.com/watch?v=M1CHPnZfFmU',
                'date': now - timedelta(days=7), 'duration_minutes': 90, 'is_live': False,
            },
            {
                'id': 'replay_2', 'title': 'Replay - Gestion du Stress',
                'description': 'Techniques de gestion du stress pour professionnels',
                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'date': now - timedelta(days=14), 'duration_minutes': 60, 'is_live': False,
            },
            {
                'id': 'replay_3', 'title': 'Replay - Communication Non Violente',
                'description': 'Les bases de la communication non violente en milieu professionnel',
                'external_url': 'https://vimeo.com/76979871',
                'date': now - timedelta(days=21), 'duration_minutes': 75, 'is_live': False,
            },
            {
                'id': 'replay_4', 'title': 'Replay - Atelier Leadership',
                'description': 'Les bases du leadership personnel et comment inspirer les autres',
                'external_url': 'https://vimeo.com/76979871',
                'date': now - timedelta(days=30), 'duration_minutes': 120, 'is_live': False,
            },
        ]

        for s in sessions:
            sid = s.pop('id')
            LiveReplaySession.objects.update_or_create(id=sid, defaults=s)

        # Session attendance
        SessionAttendance.objects.filter(user=self.user1).delete()
        # user1 joined live_1
        SessionAttendance.objects.create(
            session=LiveReplaySession.objects.get(id='live_1'),
            user=self.user1,
        )
        # user1 watched replay_1
        SessionAttendance.objects.create(
            session=LiveReplaySession.objects.get(id='replay_1'),
            user=self.user1,
        )

    # ────────────────────── TESTIMONIES ──────────────────────

    def _create_testimonies(self):
        self.stdout.write('  Creating testimonies...')

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
            tid = t.pop('id')
            Testimony.objects.update_or_create(id=tid, defaults=t)

        comments_data = [
            {'id': 'com_1', 'testimony_id': 'test_1', 'author': self.user3,
             'content': "Tout a fait d'accord Marie ! Le programme a change ma vie aussi."},
            {'id': 'com_2', 'testimony_id': 'test_1', 'author': self.user4,
             'content': 'Merci pour ce temoignage inspirant !'},
            {'id': 'com_3', 'testimony_id': 'test_3', 'author': self.user5,
             'content': 'Je confirme, les QCM sont tres bien faits.'},
            {'id': 'com_4', 'testimony_id': 'test_5', 'author': self.user3,
             'content': "L'equipe est vraiment a l'ecoute."},
        ]

        for c in comments_data:
            cid = c.pop('id')
            TestimonyComment.objects.update_or_create(id=cid, defaults=c)

        for user in [self.user1, self.user3, self.user4]:
            TestimonyReaction.objects.get_or_create(
                testimony_id='test_1', user=user, reaction_type='like',
            )

    # ────────────────────── FAQ ──────────────────────

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
            FAQItem.objects.update_or_create(
                question=faq['question'],
                defaults={'answer': faq['answer'], 'order_index': i},
            )

    # ────────────────────── CONTACT ──────────────────────

    def _create_contact(self):
        self.stdout.write('  Creating contact info...')

        ContactInfo.objects.update_or_create(
            id=1,
            defaults={
                'phone': '+22507000000',
                'email': 'contact@boosterweek.com',
                'whatsapp': '+22507000000',
            }
        )
