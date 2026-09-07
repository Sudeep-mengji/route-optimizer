import requests

def geocode_address(address):
    """
    Converts an address string into (latitude, longitude) using Nominatim.
    Returns None if not found.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "RouteOptApp/1.0 (student project)"
    }
    response = requests.get(url, params=params, headers=headers, timeout=5)
    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    return (lat, lon)