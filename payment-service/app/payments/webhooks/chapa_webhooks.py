import requests
import json
from django.conf import settings
from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
from payments.models import Payment
from payments.events import publish_payment_completed

# @csrf_exempt  # Chapa needs to be able to POST to this without a CSRF token
def chapa_webhook(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    # Chapa often sends JSON, not Form-Data. This handles both:
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    tx_ref = data.get("tx_ref")

    if not tx_ref:
        return JsonResponse({"status": "error", "message": "Missing tx_ref"}, status=400)

    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Payment not found"}, status=404)

    # Verify with Chapa
    try:
        response = requests.get(
            f"https://api.chapa.co/v1/transaction/verify/{tx_ref}",
            headers={"Authorization": f"Bearer {settings.CHAPA_SECRET}"},
            timeout=10,
        )
        response_data = response.json()
    except requests.exceptions.RequestException:
        return JsonResponse({"status": "error", "message": "Verification service unreachable"}, status=502)

    verified_status = response_data.get("data", {}).get("status")

    if response.status_code == 200 and verified_status == "success":
        if payment.status != "success":
            payment.status = "success"
            payment.save()

            publish_payment_completed("payment.completed", {
                "order_id": str(payment.order_id)
            })
    else:
        # If status is not success, it's a failure
        payment.status = "failed"
        payment.save()

        publish_payment_completed("payment.failed", {
            "order_id": str(payment.order_id)
        })

    return JsonResponse({"status": "ok"})
