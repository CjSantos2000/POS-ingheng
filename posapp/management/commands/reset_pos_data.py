from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from posapp.models import Customer, Product, SaleTransaction, StockMovement


class Command(BaseCommand):
    help = "Reset POS records by clearing inventory, customers, sales, stock movements, sessions, and cached carts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt.",
        )
        parser.add_argument(
            "--include-users",
            action="store_true",
            help="Also delete non-superuser POS users after transactional data is cleared.",
        )
        parser.add_argument(
            "--reseed",
            action="store_true",
            help="Run seed_pos_data immediately after the reset finishes.",
        )

    def handle(self, *args, **options):
        should_confirm = not options["yes"]
        include_users = options["include_users"]
        reseed = options["reseed"]

        if should_confirm:
            self.stdout.write(self.style.WARNING("This will delete products, customers, sales history, stock movements, sessions, and cached carts."))
            if include_users:
                self.stdout.write(self.style.WARNING("Non-superuser POS users will also be deleted."))
            confirmation = input("Type RESET to continue: ").strip()
            if confirmation != "RESET":
                raise CommandError("Reset cancelled.")

        user_model = get_user_model()

        with transaction.atomic():
            sale_count = SaleTransaction.objects.count()
            customer_count = Customer.objects.count()
            product_count = Product.objects.count()
            movement_count = StockMovement.objects.count()

            SaleTransaction.objects.all().delete()
            Customer.objects.all().delete()
            Product.objects.all().delete()
            StockMovement.objects.all().delete()
            Session.objects.all().delete()

            deleted_user_count = 0
            if include_users:
                deleted_user_count, _ = user_model.objects.filter(is_superuser=False).delete()

        cache.clear()

        self.stdout.write(
            self.style.SUCCESS(
                "Reset complete: "
                f"{sale_count} sale(s), {customer_count} customer(s), {product_count} product(s), "
                f"{movement_count} stock movement(s), and all sessions were removed."
            )
        )

        if include_users:
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_user_count} non-superuser user record(s)."))

        if reseed:
            self.stdout.write("Running seed_pos_data...")
            call_command("seed_pos_data")