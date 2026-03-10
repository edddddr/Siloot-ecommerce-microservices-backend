from django.urls import path
from .views import (
    CartView,
    AddItemView,
    UpdateItemView,
    RemoveItemView,
    ClearCartView,
)

urlpatterns = [

    path("cart/", CartView.as_view()),

    path("cart/items/", AddItemView.as_view()),

    path("cart/items/<uuid:item_id>/",
         UpdateItemView.as_view()),

    path("cart/items/<uuid:item_id>/remove/",
         RemoveItemView.as_view()),

    path("cart/clear/",
         ClearCartView.as_view()),
]    