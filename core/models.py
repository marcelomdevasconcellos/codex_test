from django.db import models

class Customer(models.Model):
    name  = models.CharField(max_length=200)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name


class Contract(models.Model):
    """Commercial contract information."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="contracts",
    )
    contract_number = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.contract_number


class Service(models.Model):
    """Services offered within a contract."""

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=200)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    """Billing information for a single customer and reference month."""

    WAITING = "waiting"
    PAID = "paid"
    STATUS_CHOICES = [
        (WAITING, "Waiting for payment"),
        (PAID, "Paid"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    reference_date = models.CharField(max_length=7)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Invoice {self.customer} {self.reference_date}"


class InvoiceItem(models.Model):
    """Individual service line within an invoice."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    service_name = models.CharField(max_length=200)
    service_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.service_name
