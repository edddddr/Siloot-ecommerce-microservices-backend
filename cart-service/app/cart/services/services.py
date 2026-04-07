import logging

import uuid
from django.db import transaction, IntegrityError
from cart.models import Cart, CartItem
from cart.clients.product_client import ProductClient
from cart.clients.inventory_client import InventoryClient

from django.shortcuts import get_object_or_404


logger = logging.getLogger(__name__)

from cart.exceptions import ProductNotFoundError


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
        
        try:
            available_stock = InventoryClient.get_stock(product_id)

            if available_stock is None:
                    logger.error("Could not verify stock", extra={"product_id": product_id})

            if quantity > available_stock:
                    logger.warning("Insufficient stock", extra={"product_id": product_id, "requested": quantity})
                    raise ValueError(f"Only {available_stock} items available in stock.")


            product = ProductClient.get_product(product_id)
            if not product:
                raise ProductNotFoundError(product_id)


            product_name = product["name"]
            price = product["price"]


            try:
                item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product_id=product_id,
                    product_name = product_name,
                    quantity = quantity,
                    price  = price,
                )

            except IntegrityError:
                
                item = CartItem.objects.get(cart=cart, product_id=product_id)
                created = False

            if not created:
                # If item exists, we increment the quantity instead of overwriting
                item.quantity += quantity
                # Re-check stock for the NEW total quantity
                if item.quantity > available_stock:
                    raise ValueError(f"Total quantity in cart ({item.quantity}) exceeds available stock.")
                item.save()

            logger.info(
                "Item added to cart successfully", 
                extra={"user_id": user_id, "product_id": product_id, "quantity": quantity}
            )
            return item

        except ProductNotFoundError as e:
            logger.error("Add to cart failed: Product not found", extra={"product_id": product_id})
            raise
        except ValueError as e:
            # Business logic errors (Stock, etc.)
            logger.warning("Add to cart validation failed", extra={"error": str(e)})
            raise
        except Exception as e:
            # Unexpected System Errors (Connection, etc.)
            logger.error("Critical error in add_item", extra={"error": str(e)}, exc_info=True)
            raise



    @staticmethod
    @transaction.atomic
    def update_item(cart_item_id, quantity):

        item = get_object_or_404(CartItem, id=cart_item_id)
        
        # 2. Safety check for zero or negative quantities
        if quantity <= 0:
            logger.info("Quantity set to 0, deleting item", extra={"item_id": cart_item_id})
            item.delete()
            return None

        try:
            # 3. Re-verify stock with Inventory Service (S2S)
            available_stock = InventoryClient.get_stock(item.product_id)
            
            if available_stock is None:
                raise ValueError("Inventory service unavailable. Cannot verify stock.")

            if quantity > available_stock:
                logger.warning(
                    "Update failed: Insufficient stock", 
                    extra={"product_id": item.product_id, "requested": quantity, "available": available_stock}
                )
                raise ValueError(f"Cannot update quantity. Only {available_stock} items available.")

            # 4. Save the update
            item.quantity = quantity
            item.save()
            
            logger.info(
                "Cart item updated", 
                extra={"item_id": cart_item_id, "new_quantity": quantity}
            )
            return item

        except ValueError as e:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during item update", 
                extra={"item_id": cart_item_id, "error": str(e)},
                exc_info=True
            )
            raise


    @staticmethod
    @transaction.atomic
    def remove_item(cart_item_id):

        try:
            # 1. Fetch the item (raises 404 if not found)
            item = get_object_or_404(CartItem, id=cart_item_id)
            
            # Capture data for logging before deletion
            product_id = item.product_id
            cart_id = item.cart_id

            # 2. Perform deletion
            item.delete()

            logger.info(
                "Item removed from cart", 
                extra={
                    "cart_item_id": cart_item_id, 
                    "product_id": product_id,
                    "cart_id": cart_id
                }
            )
            return True

        except Exception as e:
            # If the item is already gone, we treat it as a success (idempotency)
            # but log the event for debugging.
            logger.warning(
                "Attempted to remove non-existent cart item", 
                extra={"cart_item_id": cart_item_id, "error": str(e)}
            )
            return False


    @staticmethod
    @transaction.atomic
    def clear_cart(user_id):

        try:
            # 1. Attempt to find the cart
            cart = Cart.objects.filter(user_id=user_id).first()
            
            if not cart:
                logger.info("Clear cart skipped: No cart found", extra={"user_id": user_id})
                return False

            # 2. Bulk delete all items associated with this cart
            # This is more efficient than looping through items
            deleted_count, _ = CartItem.objects.filter(cart=cart).delete()

            logger.info(
                "Cart cleared successfully", 
                extra={
                    "user_id": user_id, 
                    "items_removed": deleted_count
                }
            )
            return True

        except Exception as e:
            logger.error(
                "Critical failure during clear_cart", 
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            raise