import uuid
from django.db import transaction
from .models import Cart, CartItem
from .clients.product_client import ProductClient
from .clients.inventory_client import InventoryClient



class CartService:

    @staticmethod
    def get_or_create_cart(user_id):


        cart, created = Cart.objects.get_or_create(
            user_id=user_id
        )

        return cart
    

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