import logging
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from inventory.models import InventoryItem


CACHE_TTL = 60  # seconds

logger = logging.getLogger(__name__)

class InventoryCache:

    @staticmethod
    def get_stock(product_id):
        cache_key = f"stock:{product_id}"
        stock = None

        # 1. Attempt to Read from Cache (with Error Handling)
        try:
            stock = cache.get(cache_key)
        except (ConnectionError, TimeoutError) as e:
            # FAIL OPEN: Log the error but don't crash. 
            # The user still gets their stock data from the DB below.
            logger.error(
                "Redis connection failed during stock GET", 
                extra={"product_id": product_id, "error": str(e)}
            )

        # 2. Cache Miss or Redis Failure logic
        if stock is None:
            try:
                # Fetch from PostgreSQL
                inventory = get_object_or_404(InventoryItem, product_id=product_id)
                stock = inventory.total_stock - inventory.reserved_stock
                
                # 3. Attempt to Update Cache (with Error Handling)
                try:
                    cache.set(cache_key, stock, timeout=3600) # 1 hour TTL
                    logger.info("Stock cache updated", extra={"product_id": product_id})
                except (ConnectionError, TimeoutError):
                    logger.warning("Failed to write updated stock to Redis")
                    
            except Exception as e:
                logger.error("Critical failure fetching stock from DB", extra={"error": str(e)})
                raise # Re-raise for the View to handle as a 500 or 404

        return stock

    @staticmethod
    def invalidate_stock(product_id):

        cache_key = f"stock:{product_id}"

        cache.delete(cache_key)