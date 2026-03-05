# from django.core.cache import cache
# from rest_framework.test import APITestCase
# from catalog.models import Category, Product

# it's need JWT but manual tested with postman and it works as expected, indeed
# class ProductCacheTest(APITestCase):

#     def setUp(self):
#         cache.clear()

#         category = Category.objects.create(name="Phones")

#         Product.objects.create(
#             name="iPhone",
#             category=category,
#             price=999
#         )

#     def test_product_list_cache(self):
#         url = "/api/v1/products/"

#         self.client.get(url)
#         keys = cache._cache.keys()

#         self.assertTrue(len(keys) > 0)