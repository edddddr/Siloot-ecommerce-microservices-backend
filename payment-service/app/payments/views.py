import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from .services import PaymentService

from .authentication import InternalServiceAuthentication
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, inline_serializer

logger = logging.getLogger(__name__)


class PaymentCreateView(APIView):

    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]
    

    def post(self, request):

        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.create_payment(
            order_id=serializer.validated_data["order_id"],
            amount=serializer.validated_data["amount"],
            currency=serializer.validated_data["currency"],
        )

        payment = PaymentService.process_payment(payment)

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )


class PaymentDetailView(APIView):
    # Ensure InternalServiceAuthentication is correctly configured in your settings
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Payment Details",
        description="Internal endpoint to fetch payment status and transaction details.",
        responses={
            200: PaymentSerializer,
            404: inline_serializer(
                name="PaymentNotFound",
                fields={"error": serializers.CharField()}
            ),
            401: inline_serializer(
                name="Unauthorized",
                fields={"detail": serializers.CharField()}
            )
        },
        auth=[{'InternalAuth': []}] 
    )
    def get(self, request, payment_id):
        """
        Fetches payment details. Used primarily by the Order Service 
        to verify transaction completion.
        """
        try:
            # 1. Fetch the payment record
            payment = Payment.objects.get(id=payment_id)
            
            # 2. Log the internal access for audit trails
            logger.info(
                "Internal payment lookup", 
                extra={
                    "payment_id": payment_id, 
                    "requested_by": request.user.username, # Should be the service name
                    "status": payment.status
                }
            )

            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Payment.DoesNotExist:
            logger.warning(
                "Payment lookup failed: Not Found", 
                extra={"payment_id": payment_id}
            )
            return Response(
                {"error": f"Payment with ID {payment_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            logger.error(
                "Unexpected error in PaymentDetailView", 
                extra={"payment_id": payment_id, "error": str(e)},
                exc_info=True
            )
            return Response(
                {"error": "Internal server error during payment lookup."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )