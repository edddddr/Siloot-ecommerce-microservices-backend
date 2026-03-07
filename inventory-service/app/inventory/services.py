import uuid
from django.db import transaction
from django.db.models import F

from .models import InventoryItem, StockReservation


class InventoryService:

    @staticmethod
    @transaction.atomic
    def reserve_stock(order_id, product_id, quantity):

        inventory = InventoryItem.objects.select_for_update().get(
            product_id=product_id
        )

        available_stock = inventory.total_stock - inventory.reserved_stock

        if available_stock < quantity:
            raise ValueError("Insufficient stock")

        inventory.reserved_stock = F("reserved_stock") + quantity
        inventory.save()

        reservation = StockReservation.objects.create(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
        )

        return reservation
    

    @staticmethod
    @transaction.atomic
    def confirm_reservation(reservation_id):

        reservation = StockReservation.objects.select_for_update().get(
            id=reservation_id
        )

        if reservation.status != StockReservation.STATUS_PENDING:
            raise ValueError("Reservation already processed")

        inventory = InventoryItem.objects.select_for_update().get(
            product_id=reservation.product_id
        )

        inventory.total_stock = F("total_stock") - reservation.quantity
        inventory.reserved_stock = F("reserved_stock") - reservation.quantity
        inventory.save()

        reservation.status = StockReservation.STATUS_CONFIRMED
        reservation.save()

        return reservation
        