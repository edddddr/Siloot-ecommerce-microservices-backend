from rest_framework.test import APITestCase


class AuthProtectionTest(APITestCase):

    def test_products_requires_auth(self):
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, 401)