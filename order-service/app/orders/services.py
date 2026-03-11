import uuid
from decimal import Decimal
from django.db import transaction

from .models import Order, OrderItem, OrderStatus, OrderStatusHistory



class OrderService:
    """
    Handles order business logic and orchestration.
    """


    @staticmethod
    @transaction.atomic
    def create_order(user_id, cart_items):
        """
        Create order and order items from cart data.
        """

        total_amount = Decimal("0.00")

        order = Order.objects.create(
            user_id=user_id,
            status=OrderStatus.CREATED,
            total_amount=Decimal("0.00")
        )

        for item in cart_items:

            product_id = item["product_id"]
            quantity = item["quantity"]
            price = Decimal(item["price"])

            OrderItem.objects.create(
                order=order,
                product_id=product_id,
                quantity=quantity,
                price=price
            )

            total_amount += price * quantity

        order.total_amount = total_amount
        order.save()

        OrderStatusHistory.objects.create(
            order=order,
            status=OrderStatus.CREATED,
            note="Order created from cart"
        )

        return order


    @staticmethod
    def update_order_status(order, new_status, note=""):
        
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            note=note
        )

        return order
