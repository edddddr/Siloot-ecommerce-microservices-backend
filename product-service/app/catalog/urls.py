from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductImageUploadView, get_explore_products

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)

urlpatterns = [
    path('products/images/', ProductImageUploadView.as_view()),
    path('products/explore', get_explore_products.as_view()),
    path('', include(router.urls))
]
