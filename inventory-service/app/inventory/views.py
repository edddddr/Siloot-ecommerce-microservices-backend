import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    ReserveStockSerializer,
    ReservationActionSerializer
)

from .services.services import InventoryService
from rest_framework import status, serializers


from .authentication import InternalServiceAuthentication  
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import api_view
from .services.cache import InventoryCache

from .exceptions import InsufficientStockError, ReservationIsProcessed

from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)

class ReserveStockView(APIView):

    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]  

    @extend_schema(
        summary="Reserve stock for an order",
        description="Internal endpoint to temporarily reserve stock during the checkout process.",
        request=ReserveStockSerializer,
        responses={
            201: inline_serializer(
                name="ReservationSuccess",
                fields={
                    "reservation_id": serializers.UUIDField(),
                    "status": serializers.CharField()
                }
            ),
            400: inline_serializer(
                name="ReservationFailed",
                fields={"error": serializers.CharField(), "details": serializers.DictField()}
            ),
            409: inline_serializer(
                name="StockConflict",
                fields={"error": serializers.CharField()}
            ),
            500: inline_serializer(
                name="InternalError",
                fields={"error": serializers.CharField()}
            )
        }
    )
    
    def post(self, request):

        order_id = request.data.get("order_id")
        product_id = request.data.get("product_id")

        logger.info(
            "Stock reservation attempt received", 
            extra={"order_id": order_id, "product_id": product_id}
        )

        try:
            serializer = ReserveStockSerializer(data=request.data)
            if not serializer.is_valid():
                    logger.warning("Reservation validation failed", extra={"errors": serializer.errors})
                    return Response(
                        {"error": "Invalid request data", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            reservation = InventoryService.reserve_stock(
                order_id=serializer.validated_data["order_id"],
                product_id=serializer.validated_data["product_id"],
                quantity=serializer.validated_data["quantity"],
            )

            logger.info(
                    "Stock reserved successfully", 
                    extra={"reservation_id": reservation.id, "order_id": order_id}
                )
            

            return Response(
                {
                    "reservation_id": reservation.id,
                    "status": reservation.status
                },
                status=status.HTTP_201_CREATED
            )

        except InsufficientStockError as e: 
            logger.warning(
                "Stock reservation rejected: Insufficient stock", 
                extra={"product_id": product_id, "order_id": order_id}
            )
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_409_CONFLICT
            )
        
        except Exception as e:
            # 4. Critical System Error
            logger.error(
                "Critical failure during stock reservation", 
                extra={"error": str(e), "order_id": order_id},
                exc_info=True
            )
            return Response(
                {"error": "Internal inventory service error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    



class ConfirmReservationView(APIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]    


    @extend_schema(
        summary="Confirm stock reservation",
        description="Finalizes the stock deduction. This should be called only after a successful payment signal.",
        request=ReservationActionSerializer,
        responses={
            200: inline_serializer(
                name="ConfirmationSuccess",
                fields={
                    "reservation_id": serializers.UUIDField(),
                    "status": serializers.CharField()
                }
            ),
            400: inline_serializer(
                name="ConfirmationError",
                fields={"error": serializers.CharField()}
            ),
            404: inline_serializer(
                name="ReservationNotFound",
                fields={"error": serializers.CharField()}
            ),
            500: inline_serializer(
                name="InternalError",
                fields={"error": serializers.CharField()}
            )
        }
    )


    def post(self, request):

        reservation_id = request.data.get("reservation_id")

        logger.info(
            "Stock confirmation attempt", 
            extra={"reservation_id": reservation_id}
        )

        try:
            serializer = ReservationActionSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(
                    "Confirmation validation failed", 
                    extra={"reservation_id": reservation_id, "errors": serializer.errors}
                )
                return Response(
                    {"error": "Invalid data provided", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            reservation = InventoryService.confirm_reservation(
                serializer.validated_data["reservation_id"]
            )

            logger.info(
                "Stock confirmed and deducted successfully", 
                extra={"reservation_id": reservation.id, "status": reservation.status}
            )

            return Response(
                {
                    "reservation_id": reservation.id,
                    "status": reservation.status
                }
            )
        
        except ReservationIsProcessed as e: # Custom exception
            logger.error(
                f"Confirmation failed: {str(e)} or expired", 
                extra={"reservation_id": reservation_id}
            )
            return Response(
                {"error": "Reservation not found or already expired"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            # Critical error (e.g., DB lock during deduction)
            logger.error(
                "Critical error during reservation confirmation", 
                extra={"error": str(e), "reservation_id": reservation_id},
                exc_info=True
            )
            return Response(
                {"error": "Internal server error during stock confirmation"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class ReleaseReservationView(APIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]    

    @extend_schema(
        summary="Release stock reservation",
        description="Reverts a temporary reservation. Call this if payment fails or the user cancels their order.",
        request=ReservationActionSerializer,
        responses={
            200: inline_serializer(
                name="ReleaseSuccess",
                fields={
                    "reservation_id": serializers.UUIDField(),
                    "status": serializers.CharField()
                }
            ),
            400: inline_serializer(
                name="ReleaseError",
                fields={"error": serializers.CharField()}
            ),
            404: inline_serializer(
                name="ReservationNotFound",
                fields={"error": serializers.CharField()}
            ),
            500: inline_serializer(
                name="InternalError",
                fields={"error": serializers.CharField()}
            )
        }
    )
    
    def post(self, request):

        reservation_id = request.data.get("reservation_id")
        
        logger.info(
            "Stock release attempt received", 
            extra={"reservation_id": reservation_id}
        )

        try:
            serializer = ReservationActionSerializer(data=request.data)
            if not serializer.is_valid():
                    logger.warning(
                        "Release validation failed", 
                        extra={"reservation_id": reservation_id, "errors": serializer.errors}
                    )
                    return Response(
                        {"error": "Invalid data", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    

            reservation = InventoryService(
                serializer.validated_data["reservation_id"]
            )

            logger.info(
                "Stock released back to inventory", 
                extra={"reservation_id": reservation.id, "status": reservation.status}
            )

            return Response(
                {
                    "reservation_id": reservation.id,
                    "status": reservation.status
                },
                status=status.HTTP_200_OK
            )

        except ReservationIsProcessed:
            # This can happen if a background task already cleaned up the expired reservation
            logger.warning(
                "Release skipped: Reservation already gone or handled", 
                extra={"reservation_id": reservation_id}
            )
            return Response(
                {"error": "Reservation not found or already released"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(
                "Critical failure during stock release", 
                extra={"error": str(e), "reservation_id": reservation_id},
                exc_info=True
            )
            return Response(
                {"error": "Internal inventory service error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



@extend_schema(
    summary="Get available stock",
    description="Returns available stock for a product (cached with Redis)."
)
@api_view(["GET"])
def get_stock(request, product_id):
    
    try:
            # 1. Attempt to get from Redis
            stock = InventoryCache.get_stock(product_id)
            
            # 2. Logic for Cache Miss
            if stock is None:
                logger.info("Stock cache MISS", extra={"product_id": product_id})
                # Fallback to Database logic if Cache is empty
                # stock = InventoryService.get_actual_stock(product_id)
                # InventoryCache.set_stock(product_id, stock)
                
                # If still not found after fallback
                return Response(
                    {"error": "Product stock information not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            logger.debug("Stock cache HIT", extra={"product_id": product_id})
            
            return Response({
                "product_id": product_id,
                "available_stock": stock
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            "Error fetching stock levels", 
            extra={"error": str(e), "product_id": product_id},
            exc_info=True
        )
        return Response(
            {"error": "Internal inventory service error"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )