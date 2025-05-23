from django.contrib import admin
from .models import Customer, Contract, Service, Invoice, InvoiceItem

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display   = ('id', 'name', 'email')
    search_fields  = ('name', 'email')
    ordering       = ('name',)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'contract_number',
        'service_count',
        'start_date',
        'end_date',
    )

    def service_count(self, obj):
        """Return the number of services linked to the contract."""
        return obj.services.count()

    service_count.short_description = "Services"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contract',
        'name',
        'value',
    )


class InvoiceItemAdminInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'reference_date',
        'total_amount',
        'status',
    )
    inlines = [InvoiceItemAdminInline]

