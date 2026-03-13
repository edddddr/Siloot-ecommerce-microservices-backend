from rest_framework import serializers
from .models import Order, OrderItem



class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_id",
            "quantity",
            "price",
        ]

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "status",
            "total_amount",
            "currency",
            "items",
            "created_at",
            "updated_at",
        ]


class OrderCreateItemSerializer(serializers.Serializer):

    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderCreateSerializer(serializers.Serializer):

    user_id = serializers.UUIDField()
    items = OrderCreateItemSerializer(many=True)
    currency = serializers.CharField(default="USD")

    def validate_items(self, value):

        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")

        return value


class PaymentResultSerializer(serializers.Serializer):

    order_id = serializers.UUIDField()