from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    ReserveStockSerializer,
    ReservationActionSerializer
)

from .services import InventoryService


from .authentication import InternalServiceAuthentication  
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import api_view
from .cache import InventoryCache

from drf_spectacular.utils import extend_schema


@extend_schema(
    summary="Reserve stock for an order",
    description="Temporarily reserves stock for a product during checkout.",
)
class ReserveStockView(APIView):

    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ReserveStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reservation = InventoryService.reserve_stock(
            order_id=serializer.validated_data["order_id"],
            product_id=serializer.validated_data["product_id"],
            quantity=serializer.validated_data["quantity"],
        )

        return Response(
            {
                "reservation_id": reservation.id,
                "status": reservation.status
            },
            status=status.HTTP_201_CREATED
        )

@extend_schema(
    summary="Confirm stock reservation",
    description="Finalizes stock deduction after successful payment."
)
class ConfirmReservationView(APIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]    

    def post(self, request):

        serializer = ReservationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reservation = InventoryService.confirm_reservation(
            serializer.validated_data["reservation_id"]
        )

        return Response(
            {
                "reservation_id": reservation.id,
                "status": reservation.status
            }
        )


@extend_schema(
    summary="Release stock reservation",
    description="Releases reserved stock when payment fails or order is cancelled."
)
class ReleaseReservationView(APIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]    

    def post(self, request):

        serializer = ReservationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reservation = InventoryService.release_reservation(
            serializer.validated_data["reservation_id"]
        )

        return Response(
            {
                "reservation_id": reservation.id,
                "status": reservation.status
            }
        )


@extend_schema(
    summary="Get available stock",
    description="Returns available stock for a product (cached with Redis)."
)
@api_view(["GET"])
def get_stock(request, product_id):

    stock = InventoryCache.get_stock(product_id)

    return Response({
        "product_id": product_id,
        "available_stock": stock
    })