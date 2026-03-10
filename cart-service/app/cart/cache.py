from django.core.cache import cache


class CartCache:

    @staticmethod
    def get_cart(user_id):
        return cache.get(f"cart:{user_id}")

    @staticmethod
    def set_cart(user_id, data):
        cache.set(f"cart:{user_id}", data, timeout=3600)

    @staticmethod
    def invalidate_cart(user_id):
        cache.delete(f"cart:{user_id}")