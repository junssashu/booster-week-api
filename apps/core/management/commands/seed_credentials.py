"""Idempotent seeder for the canonical test login credentials.

Creates / updates the seven users below with `SEED_PASSWORD`. Phone is the
USERNAME_FIELD and is unique, so it is used as the natural key — existing rows
are updated in place (no FK cascades, no orphan rows).

Run on a deployed environment:
    docker compose exec web python manage.py seed_credentials
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import User

SEED_PASSWORD = 'Test1234'

SEED_USERS = [
    # Admin (full superuser) — primary admin login
    {'phone': '+2250701000010', 'first_name': 'Admin', 'last_name': 'Booster',
     'role': 'admin', 'is_staff': True, 'is_superuser': True,
     'city': 'Abidjan', 'country': "Cote d'Ivoire"},
    # Admin assistant (read-only admin views)
    {'phone': '+2250700000022', 'first_name': 'Yann', 'last_name': 'Joe',
     'role': 'admin_assistant',
     'city': 'Abidjan', 'country': "Cote d'Ivoire"},
    # Students
    {'phone': '+2250701000001', 'first_name': 'Jean', 'last_name': 'Dupont',
     'email': 'jean.dupont@example.com', 'date_of_birth': '1990-05-15',
     'role': 'user', 'city': 'Abidjan', 'country': "Cote d'Ivoire"},
    {'phone': '+2250701000002', 'first_name': 'Marie', 'last_name': 'Kouassi',
     'role': 'user', 'city': 'Abidjan', 'country': "Cote d'Ivoire"},
    {'phone': '+2250701000003', 'first_name': 'Amadou', 'last_name': 'Diallo',
     'role': 'user', 'city': 'Abidjan', 'country': "Cote d'Ivoire"},
    {'phone': '+2250701000004', 'first_name': 'Fatou', 'last_name': 'Bamba',
     'role': 'user', 'city': 'Yamoussoukro', 'country': "Cote d'Ivoire"},
    {'phone': '+2250701000005', 'first_name': 'Kouame', 'last_name': 'Assi',
     'role': 'user', 'city': 'Bouake', 'country': "Cote d'Ivoire"},
]


class Command(BaseCommand):
    help = 'Seed canonical test login credentials (phone-keyed, idempotent).'

    def handle(self, *args, **options):
        for data in SEED_USERS:
            phone = data.pop('phone')
            user, created = User.objects.update_or_create(phone=phone, defaults=data)
            user.set_password(SEED_PASSWORD)
            user.save()
            verb = 'created' if created else 'updated'
            self.stdout.write(f'  {verb}: {phone}  role={user.role}  name={user.first_name} {user.last_name}')
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(SEED_USERS)} credentials.'))
