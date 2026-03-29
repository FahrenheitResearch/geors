# geors

Rust-powered drop-in replacement for [geopy](https://github.com/geopy/geopy) — geodesic distance, great-circle, polygon area, and more.

## Features

- **Geodesic distance** (Karney's algorithm via geographiclib-rs) — full double precision
- **Great-circle distance** (Haversine) — spherical approximation
- **Geodesic direct problem** — destination from point + bearing + distance
- **Polygon area** — geodesic polygon perimeter and area
- **Batch operations** — rayon-parallel array processing
- **Drop-in replacement** — same API as geopy.distance
- **Geocoder forwarding** — geors.geocoders transparently forwards to geopy

## Installation

```bash
pip install geors
```

## Usage

```python
from geors.distance import geodesic, great_circle

# Same API as geopy
d = geodesic((40.7128, -74.0060), (51.5074, -0.1278))
print(f"{d.km:.2f} km")      # 5570.25 km
print(f"{d.miles:.2f} miles") # 3461.36 miles

# Great circle
d = great_circle((40.7128, -74.0060), (51.5074, -0.1278))
print(f"{d.km:.2f} km")

# Batch (numpy arrays, rayon-parallel)
import numpy as np
from geors._geors.distance import geodesic_distance_batch

lat1 = np.random.uniform(-90, 90, 1_000_000)
lon1 = np.random.uniform(-180, 180, 1_000_000)
lat2 = np.random.uniform(-90, 90, 1_000_000)
lon2 = np.random.uniform(-180, 180, 1_000_000)
distances = geodesic_distance_batch(lat1, lon1, lat2, lon2)  # returns numpy array
```

## Verification

Verified against geopy and geographiclib to sub-millimeter precision:

```bash
pytest tests/test_python_compat.py -v
```

## Benchmarks

```bash
python tests/bench_distance.py
```
