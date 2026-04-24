import requests
from django.conf import settings
from django.http import JsonResponse
from payments.models import Payment
# from common.messaging.publisher import publish_event
from payments.events import publish_payment_completed

def chapa_webhook(request):
    data = request.POST
    tx_ref = data.get("tx_ref")

    payment = Payment.objects.get(tx_ref=tx_ref)

    verify_response = requests.get(
        f"https://api.chapa.co/v1/transaction/verify/{tx_ref}",
        headers={"Authorization": f"Bearer {settings.CHAPA_SECRET}"},
        timeout=10,
    )   
    verify_payload = verify_response.json()

    if not verify_response.ok or verify_payload.get("status") != "success":
        return JsonResponse({"status": "verification_failed"}, status=400)

    verified_data = verify_payload.get("data", {})
    if verified_data.get("tx_ref") != tx_ref:
        return JsonResponse({"status": "invalid_transaction"}, status=400)

    if verified_data.get("status") == "success":
        if payment.status != "success":
            payment.status = "success"
            payment.save()

            publish_payment_completed({
                "order_id": str(payment.order_id)
            })

    else:
        payment.status = "failed"
        payment.save()

        publish_payment_completed("payment.failed", {
            "order_id": str(payment.order_id)
        })

    return JsonResponse({"status": "ok"})
