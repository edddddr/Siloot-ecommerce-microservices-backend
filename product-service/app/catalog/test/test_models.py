from django.test import TestCase
from catalog.models import Category, Product


class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name="Electronics")

        self.assertEqual(category.name, "Electronics")
        self.assertIsNotNone(category.slug)


class ProductModelTest(TestCase):
    def test_product_creation(self):
        category = Category.objects.create(name="Books")

        product = Product.objects.create(
            name="Django Book",
            category=category,
            price=29.99,
        )

        self.assertEqual(product.name, "Django Book")
        self.assertEqual(product.category, category)
        self.assertIsNotNone(product.slug)