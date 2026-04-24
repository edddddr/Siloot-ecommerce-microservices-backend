import uuid
from django.db import models


class Cart(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.UUIDField(db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"

    def __str__(self):
        return f"Cart {self.id}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())



class CartItem(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    
    product_id = models.UUIDField(db_index=True)

    product_name = models.CharField(max_length=255)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    

    quantity = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = "cart_items"
        unique_together = ("cart", "product_id")

    def __str__(self):
        return f"{self.product_id} x {self.quantity}"

    @property
    def total_price(self):
        # Calculate for THIS specific item only
        return self.price * self.quantity