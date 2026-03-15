from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from .services import PaymentService

from .authentication import InternalServiceAuthentication
from rest_framework.permissions import IsAuthenticated


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

    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):

        payment = Payment.objects.get(id=payment_id)

        serializer = PaymentSerializer(payment)

        return Response(serializer.data)