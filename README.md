# geors

Rust-powered drop-in replacement for [geopy](https://github.com/geopy/geopy).

Replaces every compute-bound function in geopy with a Rust implementation using [Karney's geodesic algorithm](https://doi.org/10.1007/s00190-012-0578-z) via [geographiclib-rs](https://crates.io/crates/geographiclib-rs). I/O-bound operations (geocoding, rate limiting) forward transparently to geopy.

## Performance

Real-world workflow benchmarks, not synthetic microbenchmarks. Every result verified identical to geopy.

| Workflow | What it does | geopy | geors | Speedup |
|---|---|---|---|---|
| Airport distance matrix | 50 US airports, all 1225 pairs | 68 ms | 2.0 ms | **34x** |
| Nearest airport lookup | 1000 random queries x 50 airports | 2.8 s | 80 ms | **35x** |
| Radar coverage grid | 10K grid points x 10 NEXRAD radars | 5.3 s | 160 ms | **33x** |
| Radar coverage (batch) | Same, using numpy arrays | 5.3 s | 14 ms | **385x** |
| Delivery routing | 200-stop greedy nearest-neighbor | 1.0 s | 32 ms | **33x** |
| Range ring generation | 10 radars x 3 rings x 360 bearings | 143 ms | 7 ms | **20x** |
| Lightning proximity | 500K strikes x 20 cities (10M dists) | ~560 s | 0.3 s | **1,783x** |

```
python tests/bench_realworld.py
```

## Verification

Verified to sub-nanometer precision against geographiclib and geopy:

- **10,000 Karney GeodTest cases** -- max distance error: 7.5e-9 m (~7 nanometers), 0 cases >1mm
- **1,225 real US airport pairs** -- max error: 2.3e-12 km (0.002 nanometers)
- **190 global city routes** -- max error: 3.6e-12 km
- **5 real tornado tracks** (Moore 2013 EF5, Joplin 2011, etc.) -- path lengths and azimuths exact match
- **10 NEXRAD radar sites** -- coverage rings, range queries, all identical
- **100K random batch vs geopy spot check** -- max error: 3.7 nanometers
- **67 drop-in API compatibility tests** -- every constructor, method, operator, and property matches geopy behavior

```
pytest tests/test_realworld.py -v       # 15 real-world data tests
pytest tests/test_dropin_compat.py -v   # 67 drop-in API tests
pytest tests/test_python_compat.py -v   # 57 numerical accuracy tests
python tests/verify_accuracy.py         # 37/37 comprehensive checks
```

## Installation

```bash
pip install geors
```

## Usage

### Drop-in replacement

```python
# Before
from geopy.distance import geodesic, great_circle

# After (same API, 20-1783x faster)
from geors.distance import geodesic, great_circle
```

### Distance calculations

```python
from geors.distance import geodesic, great_circle, Distance

# Geodesic (ellipsoidal, Karney's algorithm)
d = geodesic((40.7128, -74.0060), (51.5074, -0.1278))
print(d.km)        # 5570.248...
print(d.miles)     # 3461.358...
print(d.meters)    # 5570248.4...
print(d.nautical)  # 3007.6...

# Great circle (spherical, Haversine)
d = great_circle((40.7128, -74.0060), (51.5074, -0.1278))
print(d.km)        # 5564.847...

# From units
d = Distance(miles=10)
d = geodesic(kilometers=150)

# Multi-point path distance
total = geodesic(nyc, chicago, denver, la)

# Custom ellipsoid
d = geodesic(nyc, london, ellipsoid='GRS-80')

# Destination point
pt = geodesic(miles=10).destination((34, 148), bearing=90)
print(pt.latitude, pt.longitude)

# Arithmetic
d1 + d2, d1 - d2, d * 3, d / 2, abs(d), -d
```

### Batch operations (numpy arrays, rayon-parallel)

```python
import numpy as np
from geors._geors import distance

lat1 = np.random.uniform(-90, 90, 1_000_000)
lon1 = np.random.uniform(-180, 180, 1_000_000)
lat2 = np.random.uniform(-90, 90, 1_000_000)
lon2 = np.random.uniform(-180, 180, 1_000_000)

# Returns numpy array, computed in parallel across all cores
distances = distance.geodesic_distance_batch(lat1, lon1, lat2, lon2)
```

### Geocoding (forwards to geopy)

```python
# Geocoding is I/O-bound, so we forward to geopy transparently
from geors.geocoders import Nominatim

geolocator = Nominatim(user_agent="my-app")
location = geolocator.geocode("New York City")
print(location.latitude, location.longitude)
```

## What's Rust, what's forwarded

| Component | Implementation | Why |
|---|---|---|
| `geors.distance.geodesic` | Rust (geographiclib-rs) | CPU-bound: Karney's iterative algorithm |
| `geors.distance.great_circle` | Rust | CPU-bound: Haversine trig |
| `geodesic_distance_batch` | Rust + rayon | Parallel array processing |
| `geors.geocoders.*` | Forwards to geopy | I/O-bound: HTTP API calls |
| `geors.extra.rate_limiter` | Forwards to geopy | I/O-bound: sleep/retry logic |
| Unit conversions | Rust | Simple arithmetic, zero overhead |

## Architecture

```
geors/
  crates/
    geo-math/     # High-precision math (trig in degrees, error-free sums, Accumulator)
    geors/        # Core library (geodesic, great-circle, polygon area, constants)
  src/            # PyO3 bindings (py_distance, py_geodesic, py_units)
  python/geors/   # Drop-in Python wrapper (Distance class, geocoder forwarding)
```

Built with [PyO3](https://pyo3.rs) + [maturin](https://www.maturin.rs). Wheels for Linux, macOS, and Windows.

## License

MIT
