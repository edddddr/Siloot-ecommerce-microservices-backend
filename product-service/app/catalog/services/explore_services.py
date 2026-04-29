import random
from catalog.models import Product

def get_explore_products(limit=10):
    base_qs = Product.objects.filter(
        is_active=True  
    )

    # Safety check
    total = base_qs.count()
    if total == 0:
        return Product.objects.none()

    # Split strategy
    # popular_count = int(limit * 0.5)
    new_count = int(limit * 0.3)
    random_count = limit - (new_count)

    # popular = list(
    #     base_qs.order_by('-sales_count')[:popular_count]
    # )

    new = list(
        base_qs.order_by('-created_at')[:new_count]
    )

    # Random without heavy DB load
    ids = list(base_qs.values_list('id', flat=True))
    random_ids = random.sample(ids, min(random_count, len(ids)))

    random_products = list(
        base_qs.filter(id__in=random_ids)
    )

    # Combine & shuffle slightly
    combined = new + random_products
    random.shuffle(combined)

    return combined[:limit]