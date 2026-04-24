from django.urls import path
from .views import PaymentDetailView
from  payments.webhooks import chapa_webhooks


urlpatterns = [

    # path(
    #     "payments/",
    #     PaymentCreateView.as_view(),
    #     name="create-payment"
    # ),

    # path(
    #     "payments/<uuid:payment_id>/",
    #     PaymentDetailView.as_view(),
    #     name="payment-detail"
    # ),

    path("payments/<uuid:order_id>/", PaymentDetailView.as_view()),
    path("api/v1/payments/webhook/", chapa_webhooks.chapa_webhook, name='chapa_webhook')

]   