from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Contract, Invoice, InvoiceItem


class Command(BaseCommand):
    """Create invoices for all contracts."""

    help = "Generate monthly invoices for all contracts"

    def handle(self, *args, **options):
        today = date.today()
        for contract in Contract.objects.all():
            end_date = contract.end_date
            if end_date > today:
                end_date = today
            month = contract.start_date.replace(day=1)
            last_month = end_date.replace(day=1)
            while month <= last_month:
                reference = month.strftime("%Y-%m")
                if Invoice.objects.filter(contract=contract, reference_date=reference).exists():
                    month = self._next_month(month)
                    continue

                days_in_month = monthrange(month.year, month.month)[1]
                month_start = month
                month_end = month.replace(day=days_in_month)

                charge_start = max(contract.start_date, month_start)
                charge_end = min(end_date, month_end)

                invoice = Invoice.objects.create(
                    customer=contract.customer,
                    contract=contract,
                    reference_date=reference,
                    total_amount=Decimal("0.00"),
                    status=Invoice.WAITING,
                )

                total = Decimal("0.00")
                for service in contract.services.all():
                    if charge_start == month_start and charge_end == month_end:
                        amount = service.value
                    else:
                        days = (charge_end - charge_start).days + 1
                        amount = (service.value * Decimal(days) / Decimal(days_in_month)).quantize(Decimal("0.01"))
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        service_name=service.name,
                        service_amount=amount,
                    )
                    total += amount

                invoice.total_amount = total.quantize(Decimal("0.01"))
                invoice.save()

                month = self._next_month(month)

    def _next_month(self, dt):
        if dt.month == 12:
            return dt.replace(year=dt.year + 1, month=1, day=1)
        return dt.replace(month=dt.month + 1, day=1)
