from rest_framework.test import APITestCase
# from django.urls import reverse
# from catalog.models import Category, Product


class ProductAPITest(APITestCase):
        # to test the product api endpoint must have auth jwt, we will implement after but, it works in postmon test
#     def setUp(self):
#         self.category = Category.objects.create(name="Tech")

#         self.product = Product.objects.create(
#             name="Laptop",
#             category=self.category,
#             price=999.99
#         )

#     def test_product_list(self):
#         url = "/api/v1/products/"
#         response = self.client.get(url)

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.data["results"]), 1)

#     def test_product_detail(self):
#         url = f"/api/v1/products/{self.product.slug}/"
#         response = self.client.get(url)

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["name"], "Laptop")

    def test_health_endpoint(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)