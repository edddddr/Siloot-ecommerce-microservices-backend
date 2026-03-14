from django.contrib import admin
from .models import Payment, PaymentTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order_id",
        "amount",
        "currency",
        "status",
        "created_at",
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "transaction_id",
        "provider",
        "status",
        "created_at",
    )