import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from .models import Order, OrderStatus
from .serializers import OrderSerializer, OrderCreateSerializer, PaymentResultSerializer
from .services import OrderService

from .authentication import InternalServiceAuthentication


from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, inline_serializer


logger = logging.getLogger(__name__)

class CreateOrderView(APIView):

    @extend_schema(
        summary="Create a new order",
        description=(
            "Initiates the checkout process: validates cart items, "
            "reserves inventory via S2S, and triggers the payment workflow."
        ),
        request=OrderCreateSerializer,
        responses={
            201: OrderSerializer,
            400: inline_serializer(
                name="OrderValidationError",
                fields={"error": serializers.CharField()}
            ),
            503: inline_serializer(
                name="OrderServiceUnavailable",
                fields={"error": serializers.CharField()}
            )
        },
        auth=[{'jwtAuth': []}]
    )

    def post(self, request):

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user_id = data["user_id"]

        logger.info("Order creation initiated", extra={
            "user_id": user_id,
            "item_count": len(data.get("items", []))
        })
        

        try:
            order = OrderService.create_order(
                user_id= user_id,
                cart_items=data["items"]
            )

            response = OrderSerializer(order)

            return Response(response.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Catch Business Logic errors (e.g., "Insufficient Stock")
            logger.warning("Order validation failed", extra={"user_id": user_id, "error": str(e)})
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            # Catch Infrastructure failures (Inventory down, RabbitMQ down, DB timeout)
            logger.error(
                "Order creation failed due to system error", 
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            # We use 503 Service Unavailable because this usually involves 
            # failed communication with other microservices in the EKS cluster.
            return Response(
                {"error": "Checkout is temporarily unavailable. Your cart is safe, please try again in a moment."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )



class OrderDetailView(APIView):

    @extend_schema(
        summary="Retrieve Order Details",
        description="Fetches full details for a specific order, including items and status.",
        responses={
            200: OrderSerializer,
            401: inline_serializer(name="Unauth", fields={"detail": serializers.CharField()}),
            404: inline_serializer(name="NotFound", fields={"detail": serializers.CharField()})
        },
        auth=[{'jwtAuth': []}]
    )

    def get(self, request, order_id):

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            logger.warning(
                "Unauthorized or non-existent order access attempt", 
                extra={"user_id": request.user.id, "order_id": order_id}
            )
            return Response(
                {"detail": "Order not found or you do not have permission to view it."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderSerializer(order)
        
        logger.info("Order details retrieved", extra={"order_id": order_id})
        return Response(serializer.data)


class UserOrdersView(APIView):

    @extend_schema(
        summary="List User Orders",
        description="Retrieves a history of all orders belonging to the authenticated user.",
        responses={
            200: OrderSerializer(many=True),
            403: inline_serializer(name="Forbidden", fields={"detail": serializers.CharField()})
        },
        auth=[{'jwtAuth': []}]
    )

    def get(self, request, user_id):


        orders = Order.objects.filter(user_id=user_id).order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)

        logger.info("Order history retrieved", extra={"user_id": user_id, "count": orders.count()})

        return Response(serializer.data)




# class PaymentSuccessView(APIView):

#     authentication_classes = [InternalServiceAuthentication]
#     permission_classes = [IsAuthenticated]




#     def post(self, request):

#         serializer = PaymentResultSerializer(data=request.data)

#         serializer.is_valid(raise_exception=True)

#         order_id = serializer.validated_data["order_id"]

#         try:
#             order = Order.objects.get(id=order_id)
#         except Order.DoesNotExist:
#             return Response(
#                 {"detail": "Order not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         OrderService.update_order_status(
#             order,
#             OrderStatus.PAID,
#             "Payment completed"
#         )
        

#         return Response({"message": "Order marked as paid"})



# class PaymentFailedView(APIView):

#     authentication_classes = [InternalServiceAuthentication]
#     permission_classes = [IsAuthenticated]

    
#     def post(self, request):

#         serializer = PaymentResultSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         order_id = serializer.validated_data["order_id"]

#         try:
#             order = Order.objects.get(id=order_id)
#         except Order.DoesNotExist:
#             return Response(
#                 {"detail": "Order not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         OrderService.update_order_status(
#             order,
#             OrderStatus.FAILED,
#             "Payment failed"
#         )

#         return Response({"message": "Order marked as failed"})