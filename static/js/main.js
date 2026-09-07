function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

async function loadDeliveryPoints() {
    const res = await fetch('/api/delivery-points/');
    const data = await res.json();
    const list = document.getElementById('deliveryList');
    list.innerHTML = '';
    data.forEach(dp => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${dp.address} — demand: ${dp.demand}</span>
            <button class="deleteBtn" data-type="delivery-points" data-id="${dp.id}">✕</button>
        `;
        list.appendChild(li);
    });
    document.getElementById('dpCount').textContent = data.length;
    attachDeleteHandlers();
}

async function loadVehicles() {
    const res = await fetch('/api/vehicles/');
    const data = await res.json();
    const list = document.getElementById('vehicleList');
    list.innerHTML = '';
    data.forEach(v => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${v.name} — capacity: ${v.capacity}</span>
            <button class="deleteBtn" data-type="vehicles" data-id="${v.id}">✕</button>
        `;
        list.appendChild(li);
    });
    document.getElementById('vCount').textContent = data.length;
    attachDeleteHandlers();
}

function attachDeleteHandlers() {
    document.querySelectorAll('.deleteBtn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const type = btn.dataset.type;
            const id = btn.dataset.id;
            if (!confirm('Are you sure you want to delete this?')) return;

            const res = await fetch(`/api/${type}/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrftoken }
            });

            if (res.ok) {
                if (type === 'delivery-points') loadDeliveryPoints();
                else loadVehicles();
            } else {
                alert('Failed to delete.');
            }
        });
    });
}

function showMessage(elementId, text, type) {
    const el = document.getElementById(elementId);
    el.textContent = text;
    el.className = 'form-message ' + type;
    if (type === 'success') {
        setTimeout(() => { el.textContent = ''; el.className = 'form-message'; }, 3000);
    }
}

document.getElementById('addDeliveryBtn').addEventListener('click', async () => {
    const address = document.getElementById('dpAddress').value.trim();
    const demand = document.getElementById('dpDemand').value;

    if (!address || !demand) {
        showMessage('dpMessage', 'Please fill in both address and demand.', 'error');
        return;
    }
    if (parseInt(demand) <= 0) {
        showMessage('dpMessage', 'Demand must be a positive number.', 'error');
        return;
    }

    const res = await fetch('/api/delivery-points/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ address, demand })
    });

    if (res.ok) {
        document.getElementById('dpAddress').value = '';
        document.getElementById('dpDemand').value = '';
        showMessage('dpMessage', 'Delivery point added successfully.', 'success');
        loadDeliveryPoints();
    } else {
        const err = await res.json();
        showMessage('dpMessage', 'Error: ' + (err.error || JSON.stringify(err)), 'error');
    }
});

document.getElementById('addVehicleBtn').addEventListener('click', async () => {
    const name = document.getElementById('vName').value.trim();
    const capacity = document.getElementById('vCapacity').value;

    if (!name || !capacity) {
        showMessage('vMessage', 'Please fill in both name and capacity.', 'error');
        return;
    }
    if (parseInt(capacity) <= 0) {
        showMessage('vMessage', 'Capacity must be a positive number.', 'error');
        return;
    }

    const depotRes = await fetch('/api/depots/');
    const depots = await depotRes.json();
    if (depots.length === 0) {
        showMessage('vMessage', 'No depot found. Please add a depot first via admin.', 'error');
        return;
    }

    const res = await fetch('/api/vehicles/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ name, capacity, depot: depots[0].id })
    });

    if (res.ok) {
        document.getElementById('vName').value = '';
        document.getElementById('vCapacity').value = '';
        showMessage('vMessage', 'Vehicle added successfully.', 'success');
        loadVehicles();
    } else {
        const err = await res.json();
        showMessage('vMessage', 'Error: ' + JSON.stringify(err), 'error');
    }
});

async function loadHistory() {
    const res = await fetch('/api/route-plans/');
    const data = await res.json();
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = '';

    data.forEach(plan => {
        const row = document.createElement('tr');
        const date = new Date(plan.created_at).toLocaleString();
        const improvement = plan.total_distance_naive > 0
            ? (((plan.total_distance_naive - plan.total_distance_optimized) / plan.total_distance_naive) * 100).toFixed(2)
            : '—';

        row.innerHTML = `
            <td>${plan.id}</td>
            <td>${date}</td>
            <td>${plan.total_distance_naive ?? '—'}</td>
            <td>${plan.total_distance_optimized ?? '—'}</td>
            <td>${improvement}%</td>
        `;
        tbody.appendChild(row);
    });
}


// Load lists on page load
loadDeliveryPoints();
loadVehicles();
loadHistory();

document.getElementById('clearHistoryBtn').addEventListener('click', async () => {
    if (!confirm('Clear all run history? This cannot be undone.')) return;

    const res = await fetch('/api/clear-history/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': csrftoken }
    });

    if (res.ok) {
        loadHistory();
    } else {
        alert('Failed to clear history.');
    }
});
// Initialize the map, centered roughly on Bangalore
const map = L.map('map').setView([12.9352, 77.6146], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Different colors per vehicle route
const routeColors = ['#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#1abc9c'];

let currentLayers = [];

function clearMap() {
    currentLayers.forEach(layer => map.removeLayer(layer));
    currentLayers = [];
}

document.getElementById('optimizeBtn').addEventListener('click', async () => {
    clearMap();

    const btn = document.getElementById('optimizeBtn');
    const status = document.getElementById('optimizeStatus');
    btn.disabled = true;
    btn.textContent = 'Optimizing...';
    status.style.display = 'block';

    try {
        const response = await fetch('/api/optimize/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        if (!response.ok) {
            const errData = await response.json();
            alert('Error: ' + (errData.error || 'Something went wrong'));
            return;
        }

        const data = await response.json();

        document.getElementById('naiveDist').textContent = data.total_naive_distance_km ?? 'N/A';
        document.getElementById('optDist').textContent = data.total_optimized_distance_km;
        document.getElementById('improvement').textContent = data.improvement_percent ?? 'N/A';
        document.getElementById('stats').style.display = 'flex';
        loadHistory();

        data.routes.forEach((vehicleRoute, i) => {
            const color = routeColors[i % routeColors.length];
            const latlngs = vehicleRoute.route.map(point => [point.latitude, point.longitude]);

            const polyline = L.polyline(latlngs, { color: color, weight: 4 }).addTo(map);
            currentLayers.push(polyline);

            vehicleRoute.route.forEach(point => {
                const marker = L.circleMarker([point.latitude, point.longitude], {
                    radius: 6,
                    color: color,
                    fillColor: color,
                    fillOpacity: 1
                }).addTo(map).bindPopup(`<b>${point.name}</b><br>Vehicle: ${vehicleRoute.vehicle}`);
                currentLayers.push(marker);
            });
        });

        map.fitBounds(L.featureGroup(currentLayers).getBounds(), { padding: [30, 30] });

    } catch (err) {
        alert('Request failed: ' + err.message);
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Run Optimization';
        status.style.display = 'none';
    }
});