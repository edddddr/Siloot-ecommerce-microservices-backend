from django.urls import path

from .views import (
    ReserveStockView,
    ConfirmReservationView,
    ReleaseReservationView,
    get_stock,
)

urlpatterns = [
    path("reserve/", ReserveStockView.as_view()),
    path("confirm/", ConfirmReservationView.as_view()),
    path("release/", ReleaseReservationView.as_view()),
    path("inventory/<uuid:product_id>/", get_stock),
]