from django.db import models

# Create your models here.
class Depot(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=225)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()  # max packages it can carry
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='vehicles')

    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"


class DeliveryPoint(models.Model):
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    demand = models.IntegerField() # number of packages for this delivery

    def __str__(self):
        return self.address


class RoutePlan(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    total_distance_naive = models.FloatField(null=True, blank=True)
    total_distance_optimized = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return f"RoutePlan {self.id} - {self.status}"


class RouteAssignment(models.Model):
    route_plan = models.ForeignKey(RoutePlan, on_delete=models.CASCADE, related_name='assignments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    delivery_point = models.ForeignKey(DeliveryPoint, on_delete=models.CASCADE)
    sequence_order = models.IntegerField() # order in which this point is visited

    def __str__(self):
        return f"Vehicle {self.vehicle} -> {self.delivery_point} (order {self.sequence_order})"
    