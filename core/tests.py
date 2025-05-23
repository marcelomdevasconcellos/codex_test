from django.test import TestCase, SimpleTestCase
from django.contrib.admin.sites import AdminSite
from unittest import mock
import builtins
import sys

from .models import Customer, Contract, Service
from .admin import ContractAdmin
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

