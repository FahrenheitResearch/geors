# geors

Rust-powered drop-in replacement for [geopy](https://github.com/geopy/geopy).

Replaces every compute-bound function in geopy with a Rust implementation using [Karney's geodesic algorithm](https://doi.org/10.1007/s00190-012-0578-z) via [geographiclib-rs](https://crates.io/crates/geographiclib-rs). I/O-bound operations (geocoding, rate limiting) forward transparently to geopy.

## Performance

| Operation | geopy | geors (Rust) | Speedup |
|---|---|---|---|
| Geodesic distance (scalar) | 62.5 us | 0.5 us | **125x** |
| Great-circle distance | 3.1 us | 0.1 us | **31x** |
| Full inverse (azimuths, scales) | 42.1 us | 0.8 us | **52x** |
| Direct problem | 10.8 us | 0.6 us | **18x** |
| Batch geodesic (1K points) | 59.2 ms | 0.06 ms | **1,063x** |
| Batch geodesic (10K points) | 589 ms | 0.29 ms | **2,078x** |
| Batch geodesic (1M points) | ~59 sec | 23.8 ms | **~2,500x** |

Batch throughput: **42 million point-pairs/sec** (rayon-parallel).

## Verification

Verified to sub-nanometer precision against geographiclib and geopy:

- **10,000 Karney GeodTest cases** -- max distance error: 7.5e-9 m (~7 nanometers), 0 cases >1mm
- **15 real-world city pairs** -- max error: 9.3e-10 m (<1 nanometer)
- **13 edge cases** -- identical points, poles, antipodal, antimeridian, near-antipodal (Vincenty failure cases) -- all exact match
- **1,000 random direct/inverse roundtrips** -- max error: 5.6e-9 m
- **1,000 random cross-checks vs geopy** -- max error: 5.6e-9 m
- **Batch vs scalar consistency** -- exact match (0.0 m difference)

```
pytest tests/test_python_compat.py -v     # 57 tests
python tests/verify_accuracy.py           # 37/37 comprehensive checks
python tests/bench_distance.py            # full benchmark suite
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

# After (same API, 125x faster)
from geors.distance import geodesic, great_circle
```

### Distance calculations

```python
from geors.distance import geodesic, great_circle

# Geodesic (ellipsoidal, Karney's algorithm)
d = geodesic((40.7128, -74.0060), (51.5074, -0.1278))
print(d.km)        # 5570.248...
print(d.miles)     # 3461.358...
print(d.meters)    # 5570248.4...
print(d.feet)      # 18274764.0...
print(d.nautical)  # 3007.6...

# Great circle (spherical, Haversine)
d = great_circle((40.7128, -74.0060), (51.5074, -0.1278))
print(d.km)        # 5564.847...
```

### Low-level functions

```python
from geors._geors import distance, geodesic

# Scalar
meters = distance.geodesic_distance(40.7128, -74.0060, 51.5074, -0.1278)

# Full inverse (returns dict with s12, azi1, azi2, a12, ...)
result = distance.geodesic_inverse(40.7128, -74.0060, 51.5074, -0.1278)

# Direct problem (start + bearing + distance -> endpoint)
result = geodesic.direct(40.7128, -74.0060, 51.37, 5_554_000.0)

# Destination
lat2, lon2 = distance.geodesic_destination(40.7128, -74.0060, 51.37, 5_554_000.0)
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
distances_gc = distance.great_circle_distance_batch(lat1, lon1, lat2, lon2)
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
