from django.test import TestCase, SimpleTestCase
from django.contrib.admin.sites import AdminSite
from unittest import mock
import builtins
import sys
from datetime import date
from decimal import Decimal

from .models import Customer, Contract, Service, Invoice, InvoiceItem
from .admin import ContractAdmin, InvoiceAdmin, InvoiceItemAdminInline
from manage import main as manage_main


class ModelStrTests(TestCase):
    def test_str_methods(self):
        customer = Customer.objects.create(name="ACME", email="acme@example.com")
        contract = Contract.objects.create(
            customer=customer,
            contract_number="C123",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
        service = Service.objects.create(contract=contract, name="Hosting", value=99.99)

        self.assertEqual(str(customer), "ACME")
        self.assertEqual(str(contract), "C123")
        self.assertEqual(str(service), "Hosting")

    def test_contract_admin_service_count(self):
        customer = Customer.objects.create(name="ACME", email="admin@example.com")
        contract = Contract.objects.create(
            customer=customer,
            contract_number="A1",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
        Service.objects.create(contract=contract, name="S1", value=1)
        Service.objects.create(contract=contract, name="S2", value=2)

        admin_site = AdminSite()
        admin_instance = ContractAdmin(Contract, admin_site)

        self.assertEqual(admin_instance.service_count(contract), 2)
        self.assertEqual(admin_instance.service_count.short_description, "Services")


class ManageTests(SimpleTestCase):
    def test_main_executes_command_line(self):
        with mock.patch("django.core.management.execute_from_command_line") as mock_exec:
            manage_main()
            mock_exec.assert_called_once_with(sys.argv)

    def test_main_import_error(self):
        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "django.core.management":
                raise ImportError("missing")
            return original_import(name, globals, locals, fromlist, level)

        # Call once with a different module to exercise the return path
        fake_import("sys")

        with mock.patch("builtins.__import__", side_effect=fake_import):
            with self.assertRaises(ImportError):
                manage_main()


from io import StringIO
from django.core.management import call_command
from core.management.commands.generate_invoices import Command


class FakeDataCommandTests(TestCase):
    def test_command_creates_expected_objects(self):
        out = StringIO()
        call_command('generate_fake_data', stdout=out)
        self.assertIn('Fake data generated.', out.getvalue())
        self.assertEqual(Customer.objects.count(), 10)
        for customer in Customer.objects.all():
            contract_total = customer.contracts.count()
            self.assertGreaterEqual(contract_total, 1)
            self.assertLessEqual(contract_total, 5)
            for contract in customer.contracts.all():
                service_total = contract.services.count()
                self.assertIn(service_total, (3, 4))
                self.assertLess(contract.start_date, contract.end_date)


class InvoiceTests(TestCase):
    def test_str_and_admin_integration(self):
        customer = Customer.objects.create(name="Cust", email="cust@example.com")
        contract = Contract.objects.create(
            customer=customer,
            contract_number="C001",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
        invoice = Invoice.objects.create(
            customer=customer,
            contract=contract,
            reference_date="2025-05",
            total_amount=100,
            status=Invoice.WAITING,
        )
        item = InvoiceItem.objects.create(
            invoice=invoice,
            service_name="Consulting",
            service_amount=100,
        )

        self.assertEqual(str(invoice), "Invoice Cust 2025-05")
        self.assertEqual(str(item), "Consulting")

        admin_site = AdminSite()
        invoice_admin = InvoiceAdmin(Invoice, admin_site)
        self.assertIn(InvoiceItemAdminInline, invoice_admin.inlines)
        inline_instance = InvoiceItemAdminInline(InvoiceItem, admin_site)
        self.assertEqual(inline_instance.model, InvoiceItem)


class GenerateInvoicesCommandTests(TestCase):
    def test_command_creates_invoices_without_duplicates(self):
        customer = Customer.objects.create(name="AC", email="ac@example.com")
        contract = Contract.objects.create(
            customer=customer,
            contract_number="C100",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 4, 30),
        )
        Service.objects.create(contract=contract, name="SVC", value=Decimal("31"))

        target_today = date(2024, 3, 15)

        with mock.patch("core.management.commands.generate_invoices.date") as mock_date:
            mock_date.today.return_value = target_today
            call_command("generate_invoices")

        invoices = Invoice.objects.filter(contract=contract).order_by("reference_date")
        self.assertEqual(invoices.count(), 3)
        self.assertEqual([inv.reference_date for inv in invoices], ["2024-01", "2024-02", "2024-03"])
        self.assertEqual([item.service_amount for item in invoices[0].items.all()], [Decimal("17")])
        self.assertEqual(invoices[1].total_amount, Decimal("31"))

        with mock.patch("core.management.commands.generate_invoices.date") as mock_date:
            mock_date.today.return_value = target_today
            call_command("generate_invoices")

        self.assertEqual(Invoice.objects.filter(contract=contract).count(), 3)

    def test_next_month_helper(self):
        cmd = Command()
        self.assertEqual(cmd._next_month(date(2024, 12, 1)), date(2025, 1, 1))
