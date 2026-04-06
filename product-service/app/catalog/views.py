from rest_framework import viewsets
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .pagination import ProductCursorPagination
import logging

# Permission and Authentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsAdminUserRole

# For cutsome Look up
import uuid
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, serializers

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

from drf_spectacular.utils import extend_schema, inline_serializer

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = ProductCursorPagination

    def get_object(self):

        logger.info("Category lookup initiated", extra={"lookup_value": lookup_value})
       
        queryset = self.filter_queryset(self.get_queryset())
        
        # 'pk' is the default name for the variable in the URL
        lookup_value = self.kwargs.get('pk')

        # 1. Check if the value is a valid UUID
        try:
            uuid_obj = uuid.UUID(str(lookup_value))
            # If valid UUID, look up by ID
            obj = get_object_or_404(queryset, id=uuid_obj)
        except (ValueError, AttributeError):
            # 2. If not a UUID, treat it as a slug
            obj = get_object_or_404(queryset, slug=lookup_value)
        
        except Exception as e:
            logger.error("Category lookup critical failure", extra={"error": str(e)})
            raise

        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
            summary="Create Category (Admin Only)",
            responses={
                201: CategorySerializer,
                400: inline_serializer(name="CategoryError", fields={"error": serializers.CharField()}),
                403: inline_serializer(name="Forbidden", fields={"detail": serializers.CharField()})
            }
        )
    
    def create(self, request, *args, **kwargs):
        logger.info("Category creation attempt", extra={
            "user_id": request.user.id,
            "category_name": request.data.get("name")
        })
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            logger.info("Category created successfully", extra={"category_id": serializer.data.get("id")})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            logger.warning("Category validation failed", extra={"errors": e.detail})
            return Response({"error": "Invalid data", "details": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Critical error in category creation", extra={"error": str(e)}, exc_info=True)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]        
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUserRole()]



class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer
    pagination_class = ProductCursorPagination



    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]

    def get_object(self):
        """
        Custom lookup to support both UUID (pk) and Slug
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # 'pk' is the default name for the variable in the URL
        lookup_value = self.kwargs.get('pk')

        # Debugging: See what value is coming from the URL
        
        try:
            uuid_obj = uuid.UUID(str(lookup_value))
            
            # If valid UUID, look up by ID
            obj = get_object_or_404(queryset, id=uuid_obj)
        except (ValueError, AttributeError):
            # 2. If not a UUID, treat it as a slug
            
            obj = get_object_or_404(queryset, slug=lookup_value)

        self.check_object_permissions(self.request, obj)
        return obj
      

    

    # Caching | redis 
    def list(self, request, *args, **kwargs):
        cache_key = get_product_list_cache_key(request.query_params)
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info("Product list cache HIT", extra={"cache_key": cache_key})
            return Response(cached_data)
        
        logger.info("Product list cache MISS", extra={"cache_key": cache_key})
        response = super().list(request, *args, **kwargs)

        cache_product_list(cache_key, response.data)
    
        return response
    

    def retrieve(self, request, *args, **kwargs):
    # Use 'pk' because that is what the router sends, 
    # even if the value inside is actually a slug string.
        lookup_value = kwargs.get("pk") 
        cache_key = get_product_detail_cache_key(lookup_value)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("Product detail cache HIT", extra={"product_lookup": lookup_value})
            return Response(cached_data)
        
        logger.info("Product detail cache MISS", extra={"product_lookup": lookup_value})

        try:
            response = super().retrieve(request, *args, **kwargs)
            if response.status_code == 200:
                cache_product_detail(cache_key, response.data)
            return response

        except Exception as e:
            logger.error("Product retrieval failed", extra={"error": str(e), "pk": lookup_value})
            raise
    
    @extend_schema(
        summary="Create Product (Admin Only)",
        request=ProductSerializer,
        auth=[{'jwtAuth': []}]
    )
    def create(self, request, *args, **kwargs):
        logger.info("Product creation attempt", extra={"user_id": request.user.id})
        return super().create(request, *args, **kwargs) 
    
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

    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]        
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUserRole()]
    

