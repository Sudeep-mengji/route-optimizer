from rest_framework import serializers
from .models import Depot, Vehicle, DeliveryPoint, RoutePlan, RouteAssignment


class DepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depot
        fields = '__all__'


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'


class DeliveryPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryPoint
        fields = '__all__'


class RoutePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutePlan
        fields = '__all__'