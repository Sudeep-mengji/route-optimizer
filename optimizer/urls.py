from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import optimize_routes, DepotViewSet, VehicleViewSet, DeliveryPointViewSet, RoutePlanViewSet,clear_history

router = DefaultRouter()
router.register('depots', DepotViewSet)
router.register('vehicles', VehicleViewSet)
router.register('delivery-points', DeliveryPointViewSet)
router.register('route-plans', RoutePlanViewSet)

urlpatterns = [
    path('optimize/', optimize_routes, name='optimize_routes'),
    path('clear-history/', clear_history, name='clear_history'),
    path('', include(router.urls)),
]