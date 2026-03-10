from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema


from .serializers import (
    CartSerializer,
    AddItemSerializer,
    UpdateItemSerializer,
)

from .services import CartService


from cart.cache import CartCache



class CartView(APIView):

    @extend_schema(
    description="Retrieve the user's cached or database cart.",
    responses={200: CartSerializer},
    auth=[{'BearerAuth': []}]
    )   
    def get(self, request):

       

        # if not request.user or not request.user.is_authenticated:
        #     return Response(
        #         {"error": "User not identified. Please provide a valid token."}, 
        #         status=401
        # ) 
        # else:  
        user_id = request.user

        
        cached_cart = CartCache.get_cart(user_id)

        if cached_cart:
            return Response(cached_cart)


        cart = CartService.get_or_create_cart(user_id)

        serializer = CartSerializer(cart)

        CartCache.set_cart(user_id, serializer.data)
  
        return Response(serializer.data)


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