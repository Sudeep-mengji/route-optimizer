from math import radians, sin, cos, sqrt, atan2
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/long points using the Haversine formula."""
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def build_distance_matrix(locations):
    """
    locations: list of (latitude, longitude) tuples.
    Index 0 is always the depot.
    Returns a 2D matrix of distances (in km) between every pair of locations.
    """
    size = len(locations)
    matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if i != j:
                lat1, lon1 = locations[i]
                lat2, lon2 = locations[j]
                matrix[i][j] = haversine_distance(lat1, lon1, lat2, lon2)
    return matrix


def solve_vrp(distance_matrix, demands, vehicle_capacities, num_vehicles, depot_index=0):
    """
    distance_matrix: 2D list of distances between all locations (depot + delivery points)
    demands: list of demand per location (index 0 = depot, should be 0)
    vehicle_capacities: list of capacity per vehicle (length = num_vehicles)
    num_vehicles: number of vehicles available
    depot_index: index of the depot in distance_matrix (default 0)

    Returns: dict mapping vehicle_id -> list of location indices in visiting order
    """
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 100)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        vehicle_capacities,
        True,
        'Capacity'
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return None

    routes = {}
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
        routes[vehicle_id] = route

    return routes


def naive_route(distance_matrix, demands, vehicle_capacities, num_vehicles, depot_index=0):
    """
    Naive approach: assign delivery points to vehicles in order,
    filling each vehicle to capacity before moving to the next.
    Visits points in the same fixed order (no optimization).
    """
    num_locations = len(distance_matrix)
    delivery_indices = list(range(1, num_locations))  # exclude depot

    routes = {v: [depot_index] for v in range(num_vehicles)}
    loads = {v: 0 for v in range(num_vehicles)}

    current_vehicle = 0
    for idx in delivery_indices:
        demand = demands[idx]
        # If current vehicle can't take this delivery, move to next vehicle
        while current_vehicle < num_vehicles and loads[current_vehicle] + demand > vehicle_capacities[current_vehicle]:
            current_vehicle += 1
        if current_vehicle >= num_vehicles:
            raise ValueError("Not enough vehicle capacity for naive assignment")
        routes[current_vehicle].append(idx)
        loads[current_vehicle] += demand

    # Return to depot at the end of each route
    for v in routes:
        routes[v].append(depot_index)

    return routes

def calculate_route_distance(route, distance_matrix):
    total = 0
    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i+1]]
    return total

