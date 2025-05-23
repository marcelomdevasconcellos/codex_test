from datetime import date, timedelta
import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Customer, Contract, Service


class Command(BaseCommand):
    """Generate fake customers, contracts and services."""

    help = "Create fake data for development and tests"

    def handle(self, *args, **options):
        company_prefixes = [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
            "Omega", "Apex", "Prime", "Quantum", "Nova",
        ]
        company_suffixes = ["Corp", "Ltd", "LLC", "Inc"]
        service_names = [
            "Hosting", "Support", "Consulting", "Backup",
            "Analytics", "Monitoring", "Security", "Training",
        ]

        for i in range(10):
            name = f"{random.choice(company_prefixes)} {random.choice(company_suffixes)}"
            email = f"contact{i}@example.com"
            customer = Customer.objects.create(name=name, email=email)

            for j in range(random.randint(1, 5)):
                start = date.today() - timedelta(days=random.randint(0, 365))
                end = start + timedelta(days=random.randint(30, 365))
                contract = Contract.objects.create(
                    customer=customer,
                    contract_number=f"CUST{i}-CON{j}",
                    start_date=start,
                    end_date=end,
                )

                for _ in range(random.randint(3, 4)):
                    Service.objects.create(
                        contract=contract,
                        name=random.choice(service_names),
                        value=Decimal(random.uniform(10, 1000)).quantize(Decimal("0.01")),
                    )

        self.stdout.write(self.style.SUCCESS("Fake data generated."))
