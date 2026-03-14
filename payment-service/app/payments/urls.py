from django.urls import path
from .views import PaymentCreateView, PaymentDetailView


urlpatterns = [

    path(
        "payments/",
        PaymentCreateView.as_view(),
        name="create-payment"
    ),

    path(
        "payments/<uuid:payment_id>/",
        PaymentDetailView.as_view(),
        name="payment-detail"
    ),

]   