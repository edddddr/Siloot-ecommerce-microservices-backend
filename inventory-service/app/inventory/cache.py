from django.core.cache import cache
from django.shortcuts import get_object_or_404
from .models import InventoryItem


CACHE_TTL = 60  # seconds


class InventoryCache:

    @staticmethod
    def get_stock(product_id):

        cache_key = f"stock:{product_id}"

        stock = cache.get(cache_key)

        if stock is None:

            inventory = get_object_or_404(InventoryItem, product_id=product_id)

            stock = inventory.total_stock - inventory.reserved_stock

            cache.set(cache_key, stock, CACHE_TTL)

        return stock

    @staticmethod
    def invalidate_stock(product_id):

        cache_key = f"stock:{product_id}"

        cache.delete(cache_key)