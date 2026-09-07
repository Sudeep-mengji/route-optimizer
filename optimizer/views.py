from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from .models import Depot, Vehicle, DeliveryPoint, RoutePlan, RouteAssignment
from .solver import build_distance_matrix, solve_vrp, naive_route, calculate_route_distance
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated


from rest_framework import viewsets
from .serializers import DepotSerializer, VehicleSerializer, DeliveryPointSerializer, RoutePlanSerializer
from .geocoding import geocode_address


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_routes(request):
    depot = Depot.objects.first()
    vehicles = list(Vehicle.objects.filter(depot=depot))
    points = list(DeliveryPoint.objects.all())

    if not depot or not vehicles or not points:
        return Response({"error": "Depot, vehicles, or delivery points missing."}, status=400)

    locations = [(depot.latitude, depot.longitude)] + [(p.latitude, p.longitude) for p in points]
    matrix = build_distance_matrix(locations)
    demands = [0] + [p.demand for p in points]
    vehicle_capacities = [v.capacity for v in vehicles]
    num_vehicles = len(vehicles)
    location_names = [depot.name] + [p.address for p in points]

    optimized_routes = solve_vrp(matrix, demands, vehicle_capacities, num_vehicles)
    if optimized_routes is None:
        return Response({"error": "No feasible solution. Check vehicle capacities vs total demand."}, status=400)

    try:
        naive_routes = naive_route(matrix, demands, vehicle_capacities, num_vehicles)
        total_naive = sum(calculate_route_distance(r, matrix) for r in naive_routes.values())
    except ValueError:
        # Naive baseline couldn't fit with fixed-order assignment;
        # optimized solution is still valid and shown, just skip the comparison
        naive_routes = None
        total_naive = None

    total_optimized = sum(calculate_route_distance(r, matrix) for r in optimized_routes.values())
    improvement = None
    if total_naive is not None and total_naive > 0:
        improvement = ((total_naive - total_optimized) / total_naive) * 100

    # Save this run as a RoutePlan
    route_plan = RoutePlan.objects.create(
        total_distance_naive=round(total_naive, 2) if total_naive is not None else None,
        total_distance_optimized=round(total_optimized, 2),
        status='completed'
    )

    # Save RouteAssignments for the optimized solution
    result_routes = []
    for vehicle_id, route in optimized_routes.items():
        vehicle = vehicles[vehicle_id]
        route_points = []
        for order, idx in enumerate(route):
            if idx != 0:  # skip depot entries in RouteAssignment
                delivery_point = points[idx - 1]
                RouteAssignment.objects.create(
                    route_plan=route_plan,
                    vehicle=vehicle,
                    delivery_point=delivery_point,
                    sequence_order=order
                )
            route_points.append({
                "name": location_names[idx],
                "latitude": locations[idx][0],
                "longitude": locations[idx][1]
            })
        result_routes.append({
            "vehicle": vehicle.name,
            "route": route_points
        })

    return Response({
        "route_plan_id": route_plan.id,
        "total_naive_distance_km": round(total_naive, 2) if total_naive is not None else None,
        "total_optimized_distance_km": round(total_optimized, 2),
        "improvement_percent": round(improvement, 2) if improvement is not None else None,
        "routes": result_routes
    })

@login_required(login_url='/login/')
def index(request):
    return render(request, 'index.html')





class DepotViewSet(viewsets.ModelViewSet):
    queryset = Depot.objects.all()
    serializer_class = DepotSerializer
    permission_classes = [IsAuthenticated]


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]


class DeliveryPointViewSet(viewsets.ModelViewSet):
    queryset = DeliveryPoint.objects.all()
    serializer_class = DeliveryPointSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # If lat/lon not provided but address is, auto-geocode
        data = request.data.copy()
        if 'latitude' not in data or not data.get('latitude'):
            coords = geocode_address(data.get('address', ''))
            if coords:
                data['latitude'], data['longitude'] = coords
            else:
                return Response({"error": "Could not geocode address"}, status=400)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)


class RoutePlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RoutePlan.objects.all().order_by('-created_at')
    serializer_class = RoutePlanSerializer
    permission_classes = [IsAuthenticated]

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_history(request):
    RoutePlan.objects.all().delete()
    return Response({"message": "History cleared."})