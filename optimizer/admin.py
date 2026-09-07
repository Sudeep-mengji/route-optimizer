from django.contrib import admin
from .models import Depot, Vehicle, DeliveryPoint, RouteAssignment, RoutePlan
# Register your models here.

admin.site.register(Depot)
admin.site.register(Vehicle)
admin.site.register(DeliveryPoint)
admin.site.register(RoutePlan)
admin.site.register(RouteAssignment)