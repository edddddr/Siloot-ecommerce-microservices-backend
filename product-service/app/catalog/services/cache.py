from django.core.cache import cache
from django.conf import settings


PRODUCT_LIST_TTL = 300
PRODUCT_DETAIL_TTL = 300


def get_product_list_cache_key(query_params):
    return f"product_list:{hash(frozenset(query_params.items()))}"


def get_product_detail_cache_key(slug):
    return f"product_detail:{slug}"


def cache_product_list(key, data):
    cache.set(key, data, timeout=PRODUCT_LIST_TTL)


def cache_product_detail(key, data):
    cache.set(key, data, timeout=PRODUCT_DETAIL_TTL)


def invalidate_product_cache():
    cache.delete_pattern("product_list:*")
    cache.delete_pattern("product_detail:*")