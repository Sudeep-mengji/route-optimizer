# 🚚 RouteOpt — Last-Mile Delivery Route Optimizer
[Live Demo](https://sudeepmengji.pythonanywhere.com) · [GitHub Repo](https://github.com/Sudeep-mengji/route-optimizer)

A full-stack dispatch console that solves the **Vehicle Routing Problem (VRP)** to compute optimal delivery routes across a fleet of vehicles — built with Django, Django REST Framework, Google OR-Tools, MySQL, and Leaflet.js.

RouteOpt takes a depot, a fleet of vehicles with capacity limits, and a set of delivery points with demand, and computes the most efficient set of routes to serve every delivery while respecting vehicle capacity — then benchmarks the result against a naive (non-optimized) routing approach to quantify the improvement.

**🔗 Live demo:** https://sudeepmengji.pythonanywhere.com

---

## ✨ Features

- **Real optimization engine** — Google OR-Tools solves a capacitated Vehicle Routing Problem (CVRP), not a toy heuristic.
- **Naive baseline comparison** — every optimization run is benchmarked against a simple fixed-order assignment, producing a measurable "% distance saved" metric.
- **Address geocoding** — delivery points can be added by address alone (e.g. "Whitefield, Bangalore"); coordinates are resolved automatically via the OpenStreetMap Nominatim API.
- **Interactive map visualization** — optimized routes are rendered on a live Leaflet.js map, one color per vehicle, with popups for each stop.
- **Full CRUD data management** — add/delete delivery points and vehicles directly from the UI; no need to use the Django admin panel.
- **Run history** — every optimization run is logged with its naive/optimized distances and improvement percentage, viewable in a run log table.
- **Authentication** — the entire app (frontend pages and API endpoints) is protected by Django session authentication; only logged-in dispatchers can view or modify data.
- **Graceful failure handling** — if the naive baseline can't find a valid assignment for a given dataset, the app still returns the optimized solution rather than crashing, and clearly marks the comparison as unavailable.

---

## 🧠 The Problem It Solves

Given:
- A depot (starting/ending point for all vehicles)
- A fleet of vehicles, each with a maximum carrying capacity
- A set of delivery points, each with an address and a demand (number of packages)

**Find:** the assignment of delivery points to vehicles, and the visiting order for each vehicle, that **minimizes total distance traveled** while ensuring **no vehicle exceeds its capacity**.

This is a real, well-studied combinatorial optimization problem (a generalization of the Traveling Salesman Problem) that logistics companies solve at scale every day. RouteOpt applies Google's production-grade OR-Tools constraint solver to it — rather than reinventing the algorithm from scratch, the value delivered is in correctly integrating a proven optimization library into a working, usable system.

---

## 🏗️ Architecture

```
                        ┌─────────────────────────┐
                        │   Browser (Frontend)     │
                        │  Leaflet.js map + forms  │
                        └────────────┬─────────────┘
                                     │ fetch() — JSON over HTTPS
                                     ▼
                        ┌─────────────────────────┐
                        │   Django + DRF (API)      │
                        │  ─────────────────────    │
                        │  • Auth (session + CSRF)  │
                        │  • CRUD ViewSets          │
                        │  • /api/optimize/ view    │
                        └──────┬──────────┬─────────┘
                               │          │
                 ┌─────────────┘          └─────────────┐
                 ▼                                       ▼
     ┌───────────────────────┐               ┌───────────────────────┐
     │   solver.py            │               │   geocoding.py          │
     │  • Haversine distance  │               │  • Nominatim API call   │
     │    matrix               │               │  • address → lat/long   │
     │  • OR-Tools CVRP solve │               └───────────────────────┘
     │  • Naive comparator     │
     └───────────────────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │      MySQL Database     │
     │  Depot, Vehicle,        │
     │  DeliveryPoint,          │
     │  RoutePlan,              │
     │  RouteAssignment         │
     └───────────────────────┘
```

**Request flow for an optimization run:**
1. User clicks "Run Optimization" in the browser.
2. Frontend sends `POST /api/optimize/` (with CSRF token, authenticated session).
3. Django view pulls the current Depot, Vehicles, and DeliveryPoints from MySQL.
4. `solver.py` builds a Haversine distance matrix, then calls OR-Tools to solve the CVRP.
5. The naive comparator computes a baseline route using fixed-order assignment.
6. Both results (with total distances) are saved as a `RoutePlan` + `RouteAssignment` records, and returned as JSON.
7. Frontend draws the optimized routes on the Leaflet map and updates the stats/history table.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 5.x |
| API layer | Django REST Framework |
| Database | MySQL |
| Optimization engine | Google OR-Tools (constraint_solver / routing) |
| Geocoding | OpenStreetMap Nominatim API |
| Frontend | HTML, CSS, vanilla JavaScript |
| Map rendering | Leaflet.js + OpenStreetMap tiles |
| Auth | Django session authentication + CSRF protection |

---

## 📂 Project Structure

```
route_optimizer project/
├── manage.py
├── routeopt_backend/          # Django project settings
│   ├── settings.py
│   └── urls.py                # Root URLs: admin, index, login/logout, /api/
├── optimizer/                 # Main app
│   ├── models.py              # Depot, Vehicle, DeliveryPoint, RoutePlan, RouteAssignment
│   ├── admin.py                # Django admin registration
│   ├── serializers.py          # DRF serializers for all models
│   ├── views.py                # ViewSets + optimize_routes + clear_history + index
│   ├── urls.py                 # /api/ routes (router + custom endpoints)
│   ├── solver.py               # Haversine matrix, OR-Tools solve, naive comparator
│   └── geocoding.py            # Nominatim address → lat/long lookup
├── templates/
│   ├── index.html              # Main dispatch console UI
│   └── login.html              # Login page
└── static/
    ├── css/style.css           # Dispatch console visual theme
    └── js/main.js               # Frontend logic (fetch calls, map rendering, forms)
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- MySQL Server (8.0.x recommended — see note below)
- pip

### 1. Clone and set up a virtual environment
```bash
git clone https://github.com/Sudeep-mengji/route-optimizer.git
cd route_optimizer_project
cd route-optimizer
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies
```bash
pip install django "django<6.0" djangorestframework mysqlclient ortools requests
```
> **Note:** Django 6.x requires MySQL 8.4+. If you're on MySQL 8.0.x, pin Django to `<6.0`.

### 3. Create the MySQL database
```sql
CREATE DATABASE routeopt_db;
```

### 4. Configure database credentials
In `routeopt_backend/settings.py`, update the `DATABASES` section with your MySQL username/password.

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create an admin user
```bash
python manage.py createsuperuser
```

### 7. Run the server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/login/`, log in, and add a depot, vehicles, and delivery points via the admin panel (`/admin/`) or the in-app forms.

---

## 🔌 API Endpoints

All endpoints below require authentication (Django session + CSRF token).

| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/api/depots/` | List / create depots |
| `GET/POST` | `/api/vehicles/` | List / create vehicles |
| `GET/POST` | `/api/delivery-points/` | List / create delivery points (auto-geocodes if lat/long omitted) |
| `DELETE` | `/api/delivery-points/<id>/` | Delete a delivery point |
| `DELETE` | `/api/vehicles/<id>/` | Delete a vehicle |
| `GET` | `/api/route-plans/` | List past optimization runs (latest 15) |
| `POST` | `/api/optimize/` | Run the VRP solver; returns optimized + naive routes, distances, and improvement % |
| `DELETE` | `/api/clear-history/` | Delete all logged run history |

### Example response — `POST /api/optimize/`
```json
{
  "route_plan_id": 22,
  "total_naive_distance_km": 84.59,
  "total_optimized_distance_km": 62.75,
  "improvement_percent": 25.82,
  "routes": [
    {
      "vehicle": "Truck A",
      "route": [
        {"name": "Koramangala Warehouse", "latitude": 12.9352, "longitude": 77.6146},
        {"name": "Indiranagar", "latitude": 12.9784, "longitude": 77.6408},
        {"name": "Koramangala Warehouse", "latitude": 12.9352, "longitude": 77.6146}
      ]
    }
  ]
}
```

---

## 🧮 Algorithm Notes

- **Distance metric:** straight-line (Haversine) distance between coordinates, not real road distance. This keeps the solver fast and dependency-free; swapping in a real routing API (OSRM/Google Directions) is a natural extension.
- **Solver strategy:** OR-Tools' `PATH_CHEAPEST_ARC` first-solution strategy, with a capacity dimension constraint (`AddDimensionWithVehicleCapacity`) enforcing that no vehicle's cumulative load exceeds its capacity.
- **Naive baseline:** delivery points are assigned to vehicles in database insertion order, filling one vehicle to capacity before moving to the next, and visited in that same fixed order — no distance-awareness. This baseline can occasionally fail to find *any* valid assignment for a dataset that OR-Tools can still solve (since it can't rearrange), which is itself a useful illustration of why naive/manual dispatching is inferior to constraint-based optimization. When this happens, the app still returns the OR-Tools solution and simply omits the comparison rather than failing.

---

## 🚀 Possible Extensions

- Real road-distance routing via OSRM or a directions API, instead of straight-line distance
- Time-window constraints (e.g., "deliver between 2–4 PM")
- Multiple depots
- Driver-facing mobile view
- Deployment to a live host (Render/Railway) with a managed MySQL instance

---

## 📸 Screenshots

*(Add screenshots of the dispatch console, map view, and run log here before submission.)*

---

## 👤 Author

Built by Sudeep — MCA student, as an industry-level placement project demonstrating full-stack development (Django/DRF/MySQL), applied operations research (Google OR-Tools), and real-world API integration (geocoding).
