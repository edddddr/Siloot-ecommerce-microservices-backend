from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderStatus
from .serializers import OrderSerializer, OrderCreateSerializer, PaymentResultSerializer
from .services import OrderService

from .authentication import InternalServiceAuthentication


from rest_framework.permissions import IsAuthenticated



class CreateOrderView(APIView):

    def post(self, request):

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        order = OrderService.create_order(
            user_id=data["user_id"],
            cart_items=data["items"]
        )

        response = OrderSerializer(order)

        return Response(response.data, status=status.HTTP_201_CREATED)



class OrderDetailView(APIView):

    def get(self, request, order_id):

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderSerializer(order)

        return Response(serializer.data)


class UserOrdersView(APIView):

    def get(self, request, user_id):


        orders = Order.objects.filter(user_id=user_id)

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)


class PaymentSuccessView(APIView):

    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]


    def post(self, request):

        serializer = PaymentResultSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        OrderService.update_order_status(
            order,
            OrderStatus.PAID,
            "Payment completed"
        )

        return Response({"message": "Order marked as paid"})



class PaymentFailedView(APIView):

    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]

    
    def post(self, request):

        serializer = PaymentResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        OrderService.update_order_status(
            order,
            OrderStatus.FAILED,
            "Payment failed"
        )

        return Response({"message": "Order marked as failed"})