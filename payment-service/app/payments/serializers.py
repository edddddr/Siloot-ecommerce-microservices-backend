from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_id",
            "amount",
            "currency",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class PaymentCreateSerializer(serializers.Serializer):

    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default="USD")
