import uuid
from decimal import Decimal
from django.db import transaction

from .models import Order, OrderItem, OrderStatus, OrderStatusHistory
from .integrations.inventory_client import InventoryClient
from .integrations.payment_client import PaymentClient



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

        reservations = OrderService.build_inventory_reservation(order)

        InventoryClient.reserve_stock(reservations)

        OrderService.update_order_status(
            order,
            OrderStatus.PENDING_PAYMENT,
            "Inventory reserved successfully"
        )

        payment_payload = OrderService.build_payment_payload(order)

        PaymentClient.start_payment(payment_payload)

        

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



    @staticmethod
    def build_inventory_reservation(order):

        reservations = []

        for item in order.items.all():

            reservations.append({
                "order_id": str(order.id),
                "product_id": str(item.product_id),
                "quantity": item.quantity
            })

        return reservations

        

    @staticmethod
    def build_payment_payload(order):

        return {
            "order_id": str(order.id),
            "amount": str(order.total_amount),
            "currency": order.currency
        }