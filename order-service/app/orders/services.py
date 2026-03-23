# import uuid
# from decimal import Decimal
# from django.db import transaction

# from .models import Order, OrderItem, OrderStatus, OrderStatusHistory
# from .integrations.inventory_client import InventoryClient
# from .integrations.payment_client import PaymentClient


    
# class OrderService:
#     """
#     Handles order business logic and orchestration.
#     """


#     @staticmethod
#     @transaction.atomic
#     def create_order(user_id, cart_items, currency="USD"):
    
#         # 1. Pre-calculate the total and prepare item data
#         total_amount = Decimal("0.00")
#         order_items_to_create = []

#         for item in cart_items:
#             price = Decimal(str(item["price"]))
#             quantity = int(item["quantity"])
#             total_amount += price * quantity
            
#             # We don't save yet, just prepare the objects in memory
#             order_items_to_create.append({
#                 "product_id": item["product_id"],
#                 "quantity": quantity,
#                 "price": price
#             })

#         # 2. Create the Order with the FINAL total and currency
#         order = Order.objects.create(
#             user_id=user_id,
#             status=OrderStatus.CREATED,
#             total_amount=total_amount,
#             currency=currency
#         )

#         # 3. Bulk Create the OrderItems (Better performance than a loop)
#         OrderItem.objects.bulk_create([
#             OrderItem(order=order, **item_data) 
#             for item_data in order_items_to_create
#         ])

#         # 4. Handle External Microservice calls
#         # Now 'order' has the correct total_amount for the payment payload
#         try:
#             reservations = OrderService.build_inventory_reservation(order)
#             print("\n",{"reservation : ":reservations}, "\n")
#             InventoryClient.reserve_stock(reservations)

#             OrderService.update_order_status(
#                 order,
#                 OrderStatus.PENDING_PAYMENT,
#                 "Inventory reserved successfully"
#             )

#             payment_payload = OrderService.build_payment_payload(order)
#             # print("\n", {"payment_payload : ": payment_payload})
#             transaction.on_commit(lambda: PaymentClient.start_payment(payment_payload))
#             # PaymentClient.start_payment(payment_payload)

#         except Exception as e:
#             # In a real system, you'd handle rollback/compensation here
#             raise e

#         # 5. Log History
#         OrderStatusHistory.objects.create(
#             order=order,
#             status=OrderStatus.CREATED,
#             note="Order created and payment initiated"
#         )

#         return order


#     @staticmethod
#     def update_order_status(order, new_status, note=""):
        
#         order.status = new_status
#         order.save(update_fields=["status", "updated_at"])

#         OrderStatusHistory.objects.create(
#             order=order,
#             status=new_status,
#             note=note
#         )

#         return order



#     @staticmethod
#     def build_inventory_reservation(order):

#         reservations = []

#         for item in order.items.all():

#             reservations.append({
#                 "order_id": str(order.id),
#                 "product_id": str(item.product_id),
#                 "quantity": item.quantity
#             })

#         return reservations

        

#     @staticmethod
#     def build_payment_payload(order):

#         return {
#             "order_id": str(order.id),
#             "amount": str(order.total_amount),
#             "currency": order.currency
#         }