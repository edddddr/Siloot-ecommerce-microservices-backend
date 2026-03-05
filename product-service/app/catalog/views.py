from rest_framework import viewsets
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .pagination import ProductCursorPagination

# Permission and Authentication
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUserRole

# caching
from django.core.cache import cache
from rest_framework.response import Response
from .services.cache import (
    get_product_list_cache_key,
    cache_product_list,
    get_product_detail_cache_key,
    cache_product_detail,
)
from .services.cache import invalidate_product_cache


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    pagination_class = ProductCursorPagination

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUserRole()]
        return [IsAuthenticated()]

class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer
    lookup_field = "slug"
    pagination_class = ProductCursorPagination


    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUserRole()]
        return [IsAuthenticated()]
    
    
    def list(self, request, *args, **kwargs):
        cache_key = get_product_list_cache_key(request.query_params)
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        cache_product_list(cache_key, response.data)

        return response
    

    def retrieve(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        cache_key = get_product_detail_cache_key(slug)
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        cache_product_detail(cache_key, response.data)

        return response
    
    def perform_create(self, serializer):
        instance = serializer.save()
        invalidate_product_cache()
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        invalidate_product_cache()
        return instance

    def perform_destroy(self, instance):
        instance.delete()
        invalidate_product_cache()