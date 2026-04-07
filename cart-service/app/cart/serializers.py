from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = [
            # "id",
            "product_id",
            "product_name",
            "quantity",
            "price",
            "created_at",
            "total_price",
        ]
        # read_only_fields = ['total_price']


class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "user_id",
            "items",
            "created_at",
            "updated_at",
        ]



class AddItemSerializer(serializers.Serializer):

    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateItemSerializer(serializers.Serializer):

    quantity = serializers.IntegerField(min_value=1)



class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class ReservationNotFoundErrorSerializer(serializers.Serializer):
    error = serializers.CharField()