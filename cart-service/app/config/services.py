import logging

import uuid
from django.db import transaction, IntegrityError
from .models import Cart, CartItem
from .clients.product_client import ProductClient
from .clients.inventory_client import InventoryClient

logger = logging.getLogger(__name__)



class CartService:

    @staticmethod
    def get_or_create_cart(user_id):

        try:
            cart, created = Cart.objects.get_or_create(
                user_id=user_id
            )

            if created:
                logger.info("New cart created for user", extra={"user_id": user_id})

            return cart
        
        except Cart.MultipleObjectsReturned:
            # 2. Safety Valve: If a race condition created two carts, grab the most recent one
            logger.warning(
                "Duplicate carts found for user - resolving to latest", 
                extra={"user_id": user_id}
            )
            return Cart.objects.filter(user_id=user_id).order_by("-created_at").first()

        except IntegrityError as e:
            # 3. Race Condition Handling: Another thread created it between our 'get' and 'create'
            logger.info(
                "IntegrityError during cart creation (Race Condition)", 
                extra={"user_id": user_id, "error": str(e)}
            )
            # Re-fetch now that it definitely exists
            return Cart.objects.get(user_id=user_id)

        except Exception as e:
            # 4. Critical Failure (DB Down, etc.)
            logger.error(
                "Critical failure in CartService.get_or_create_cart", 
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            raise

    @staticmethod
    @transaction.atomic
    def add_item(user_id, product_id, quantity):


        cart = CartService.get_or_create_cart(user_id)

        product = ProductClient.get_product(product_id)

        available_stock = InventoryClient.get_stock(product_id)

        if quantity > available_stock:
            raise ValueError("Not enough stock available")

        product = ProductClient.get_product(product_id)

        print("/n", product["name"], "/n", product["price"])

        product_name = product["name"]
        price = product["price"]

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            product_name = product_name,
            quantity = quantity,
            price  = price,
        )

        print(item)

        if not created:
            # item.quantity += quantity
            item.save()

        return item



    @staticmethod
    @transaction.atomic
    def update_item(cart_item_id, quantity):

        item = CartItem.objects.get(id=cart_item_id)

        item.quantity = quantity
        item.save()

        return item


    @staticmethod
    @transaction.atomic
    def remove_item(cart_item_id):

        item = CartItem.objects.get(id=cart_item_id)

        item.delete()


    @staticmethod
    @transaction.atomic
    def clear_cart(user_id):

        cart = Cart.objects.get(user_id=user_id)

        CartItem.objects.filter(cart=cart).delete()