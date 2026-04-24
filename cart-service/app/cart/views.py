import logging 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from drf_spectacular.utils import extend_schema


from .serializers import (
    CartSerializer,
    AddItemSerializer,
    ErrorResponseSerializer,
    UpdateItemSerializer,
)

from cart.services.services import CartService


from cart.cache import CartCache

from .exceptions import ProductNotFoundError

from drf_spectacular.utils import extend_schema, inline_serializer


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

        user_id = request.user.id
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
        summary="Add item to cart",
        description="Validates stock and product details before adding an item to the user's cart.",
        request=AddItemSerializer,
        responses={
            201: inline_serializer(
                name="AddItemSuccess",
                fields={"item_id": serializers.UUIDField(), "message": serializers.CharField()}
            ),
            400: inline_serializer(
                name="ValidationError",
                fields={"error": serializers.CharField()}
            ),
            404: inline_serializer(
                name="ProductNotFound",
                fields={"error": serializers.CharField()}
            ),
            503: inline_serializer(
                name="ServiceUnavailable",
                fields={"error": serializers.CharField()}
            )
        },
        auth=[{'jwtAuth': []}] # Consistent with your spectacular settings
    )

    def post(self, request):
        
        user_id = request.user.id




        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        logger.info("Add to cart request", extra={
            "user_id": user_id, 
            "product_id": product_id, 
            "quantity": quantity
        })

        try:

            item = CartService.add_item(
                user_id=user_id,
                product_id=serializer.validated_data["product_id"],
                quantity=serializer.validated_data["quantity"],
            )

            CartCache.invalidate_cart(user_id)

            return Response(
                {
                    "item_id": item.id,
                    "message": "Item added to cart successfully."
                },
                status=status.HTTP_201_CREATED
            )
            
        except ProductNotFoundError as e:
            logger.warning("Add to cart failed: Product 404", extra={"product_id": product_id})
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            # This catches "Not enough stock" or business logic errors
            logger.warning("Add to cart validation failed", extra={"error": str(e), "user_id": user_id})
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Catches S2S timeouts, connection errors, or DB failures
            logger.error(
                "Critical failure in Add to Cart View", 
                extra={"error": str(e), "user_id": user_id}, 
                exc_info=True
            )
            return Response(
                {"error": "Internal service communication error. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        



class UpdateItemView(APIView):

    @extend_schema(
        summary="Update item quantity",
        description="Updates the quantity of an item in the cart after re-verifying stock levels.",
        request=UpdateItemSerializer,
        responses={
            200: inline_serializer(
                name="UpdateSuccess",
                fields={"item_id": serializers.UUIDField(), "status": serializers.CharField()}
            ),
            400: inline_serializer(
                name="StockError",
                fields={"error": serializers.CharField()}
            ),
            404: inline_serializer(
                name="ItemNotFound",
                fields={"error": serializers.CharField()}
            )
        },
        auth=[{'jwtAuth': []}] 
    ) 
    

    def patch(self, request, item_id):

        user_id = request.user.id

        serializer = UpdateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_quantity = serializer.validated_data["quantity"]
        
        logger.info("Cart item update request", extra={
            "user_id": user_id, 
            "item_id": item_id, 
            "new_quantity": new_quantity
        })

        try:
            item = CartService.update_item(
                cart_item_id=item_id,
                quantity=new_quantity,
            )

            CartCache.invalidate_cart(user_id)


            if item is None:
                return Response(
                    {"message": "Item removed from cart."}, 
                    status=status.HTTP_200_OK
                )

            return Response(
                {"item_id": item.id, "status": "updated"},
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            # This catches "Insufficient stock" from the InventoryClient
            logger.warning("Update failed: Stock conflict", extra={"error": str(e)})
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Catches 404s (item not found) or S2S communication failures
            logger.error(
                "Critical failure in Cart Patch View", 
                extra={"error": str(e), "item_id": item_id}, 
                exc_info=True
            )
            return Response(
                {"error": "Could not update item. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RemoveItemView(APIView):
    @extend_schema(
        summary="Remove item from cart",
        description="Permanently deletes a specific item from the user's cart and invalidates the Redis cache.",
        responses={
            204: None,  # Standard for successful deletion
            404: inline_serializer(
                name="DeleteError",
                fields={"error": serializers.CharField()}
            )
        },
        auth=[{'jwtAuth': []}] # Consistent with your spectacular settings
    )

    def delete(self, request, item_id):

        user_id = request.user.id

        logger.info("Cart item deletion requested", extra={
            "user_id": user_id,
            "cart_item_id": item_id 
        })

        try:
            CartService.remove_item(item_id)
            CartCache.invalidate_cart(user_id)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(
                "Unexpected error during cart item deletion", 
                extra={"error": str(e), "item_id": item_id},
                exc_info=True
            )
            return Response(
                {"error": "Could not remove item. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearCartView(APIView):
    @extend_schema(
        summary="Clear entire cart",
        description="Removes all items from the authenticated user's cart and invalidates the Redis cache.",
        responses={
            204: None, # Standard REST response for successful bulk deletion
            500: inline_serializer(
                name="ClearError",
                fields={"error": serializers.CharField()}
            )
        },
        auth=[{'jwtAuth': []}] # Matching your established Swagger security scheme
    )

    def delete(self, request):
        
        user_id = request.user.id 

        logger.info("Bulk cart clear requested", extra={"user_id": user_id})

        try:
            
            CartService.clear_cart(user_id)


            CartCache.invalidate_cart(user_id)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(
                "Critical failure during bulk cart clear", 
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            return Response(
                {"error": "Failed to clear cart. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )