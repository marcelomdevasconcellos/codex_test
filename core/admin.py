from django.contrib import admin
from .models import Customer, Contract, Service

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
        'start_date',
        'end_date',
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contract',
        'name',
        'value',
    )

