from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from posapp.models import Product
from posapp.services import import_products


class Command(BaseCommand):
    help = "Load sample POS products and default users."

    def handle(self, *args, **options):
        seed_file = Path(settings.BASE_DIR) / "seed_data" / "products.csv"
        if not seed_file.exists():
            self.stderr.write(self.style.ERROR(f"Seed file not found: {seed_file}"))
            return

        with seed_file.open("r", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))

        imported = import_products(rows)
        self.stdout.write(self.style.SUCCESS(f"Imported {imported} products."))

        user_model = get_user_model()
        admin_user, _ = user_model.objects.get_or_create(
            username="admin",
            defaults={"role": user_model.Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        admin_user.set_password("admin12345")
        admin_user.save()

        cashier_user, _ = user_model.objects.get_or_create(
            username="cashier",
            defaults={"role": user_model.Role.CASHIER, "is_staff": False},
        )
        cashier_user.set_password("cashier12345")
        cashier_user.save()

        self.stdout.write(self.style.SUCCESS("Created default users: admin / cashier"))
