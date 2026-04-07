import logging 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema


from .serializers import (
    CartSerializer,
    AddItemSerializer,
    ErrorResponseSerializer,
    UpdateItemSerializer,
)

from .services import CartService


from cart.cache import CartCache


logger = logging.getLogger(__name__)


class CartView(APIView):

    @extend_schema(
        summary="Retrieve Cart",
        description="Fetch the user's cart from Redis cache or fallback to the database.",
        responses={
            200: CartSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        auth=[{'jwtAuth': []}] # Changed to match your established jwtAuth name
    )
    
    def get(self, request):

        user_id = request.user
        cached_cart = None

        try:
            
            cached_cart = CartCache.get_cart(user_id)

        except (ConnectionError, TimeoutError) as e:
            logger.error(
                "Redis failure during Cart GET", 
                extra={"user_id": user_id, "error": str(e)}
            )
        if cached_cart:
            logger.debug("Cart cache HIT", extra={"user_id": user_id})
            return Response(cached_cart)

        logger.info("Cart cache MISS", extra={"user_id": user_id})

        try:
            cart = CartService.get_or_create_cart(user_id)

            serializer = CartSerializer(cart)


            try:
                CartCache.set_cart(user_id, serializer.data)
            except (ConnectionError, TimeoutError):
                logger.warning("Failed to update Cart cache after DB fetch", extra={"user_id": user_id})

  
            return Response(serializer.data)

        except Exception as e:
            logger.error(
                "Critical failure retrieving cart from DB", 
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            return Response(
                {"error": "Could not retrieve your cart. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AddItemView(APIView):

    @extend_schema(
    description="Add Item to the cart.",
    responses={200: AddItemSerializer},
    auth=[{'BearerAuth': []}]
    )   

    def post(self, request):
        
        user_id = request.user




        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:

            item = CartService.add_item(
                user_id=user_id,
                product_id=serializer.validated_data["product_id"],
                quantity=serializer.validated_data["quantity"],
            )

            print(user_id, serializer.validated_data["product_id"], serializer.validated_data["quantity"])

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=400
            )
        
        CartCache.invalidate_cart(user_id)

        return Response(
            {"item_id": item.id},
            status=201
        )


class UpdateItemView(APIView):

    @extend_schema(
    description="Update Item.",
    responses={200: UpdateItemSerializer},
    auth=[{'BearerAuth': []}]
    ) 
    

    def patch(self, request, item_id):

        user_id = request.user

        serializer = UpdateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item = CartService.update_item(
            cart_item_id=item_id,
            quantity=serializer.validated_data["quantity"],
        )

        CartCache.invalidate_cart(user_id)

        return Response({"item_id": item.id})


class RemoveItemView(APIView):
    @extend_schema(
        summary="Remove item from cart",
        description="Deletes a specific item from the user's cart using the item ID and invalidates the cache.",
        responses={204: None},  # Explicitly states there is no response body
        auth=[{'BearerAuth': []}]
    )

    def delete(self, request, item_id):

        user_id = request.user

        CartService.remove_item(item_id)
        CartCache.invalidate_cart(user_id)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClearCartView(APIView):
    @extend_schema(
        summary="Clear entire cart",
        description="Removes all items from the authenticated user's cart and invalidates the cache.",
        responses={204: None},  # No content returned on success
        auth=[{'BearerAuth': []}]
    )

    def delete(self, request):

        user_id = request.user

        CartService.clear_cart(user_id)
        CartCache.invalidate_cart(user_id)

        return Response(status=status.HTTP_204_NO_CONTENT)