"""
Benchmark: geors vs geopy distance calculations.

Run: python tests/bench_distance.py
"""

import time
import numpy as np

# Reference
from geopy.distance import geodesic as geopy_geodesic
from geopy.distance import great_circle as geopy_great_circle
from geographiclib.geodesic import Geodesic as GeographiclibGeodesic

# Ours
from geors._geors import distance as _dist
geodesic_distance = _dist.geodesic_distance
great_circle_distance = _dist.great_circle_distance
geodesic_distance_batch = _dist.geodesic_distance_batch
great_circle_distance_batch = _dist.great_circle_distance_batch
geodesic_destination = _dist.geodesic_destination
geodesic_inverse = _dist.geodesic_inverse

from geors._geors import geodesic as _geo
inverse = _geo.inverse
direct = _geo.direct


def bench(name, fn, n_iter=10000, warmup=100):
    """Benchmark a function, return median time in microseconds."""
    for _ in range(warmup):
        fn()

    times = []
    for _ in range(n_iter):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000.0)  # ns -> µs

    times.sort()
    median = times[len(times) // 2]
    return median


def main():
    print("=" * 72)
    print("geors Benchmark -- Rust vs geopy/geographiclib")
    print("=" * 72)

    # Test points
    jfk = (40.6413, -73.7781)
    lhr = (51.4700, -0.4543)

    # --- Scalar geodesic distance ---
    print("\n--- Scalar Geodesic Distance (JFK -> LHR) ---")

    t_geopy = bench("geopy.geodesic", lambda: geopy_geodesic(jfk, lhr).meters)
    t_glib = bench(
        "geographiclib.Inverse",
        lambda: GeographiclibGeodesic.WGS84.Inverse(*jfk, *lhr)["s12"],
    )
    t_rust = bench(
        "geors.geodesic_distance",
        lambda: geodesic_distance(*jfk, *lhr),
    )

    print(f"  geopy.geodesic:           {t_geopy:8.2f} µs")
    print(f"  geographiclib.Inverse:    {t_glib:8.2f} µs")
    print(f"  geors (Rust):             {t_rust:8.2f} µs")
    print(f"  Speedup vs geopy:         {t_geopy / t_rust:8.1f}x")
    print(f"  Speedup vs geographiclib: {t_glib / t_rust:8.1f}x")

    # --- Scalar great-circle ---
    print("\n--- Scalar Great-Circle Distance (JFK -> LHR) ---")

    t_geopy_gc = bench("geopy.great_circle", lambda: geopy_great_circle(jfk, lhr).meters)
    t_rust_gc = bench(
        "geors.great_circle",
        lambda: great_circle_distance(*jfk, *lhr),
    )

    print(f"  geopy.great_circle:       {t_geopy_gc:8.2f} µs")
    print(f"  geors (Rust):             {t_rust_gc:8.2f} µs")
    print(f"  Speedup:                  {t_geopy_gc / t_rust_gc:8.1f}x")

    # --- Full inverse ---
    print("\n--- Full Inverse (with azimuths, etc.) ---")

    t_glib_inv = bench(
        "geographiclib.Inverse",
        lambda: GeographiclibGeodesic.WGS84.Inverse(*jfk, *lhr),
    )
    t_rust_inv = bench("geors.inverse", lambda: geodesic_inverse(*jfk, *lhr))

    print(f"  geographiclib.Inverse:    {t_glib_inv:8.2f} µs")
    print(f"  geors.inverse:            {t_rust_inv:8.2f} µs")
    print(f"  Speedup:                  {t_glib_inv / t_rust_inv:8.1f}x")

    # --- Direct problem ---
    print("\n--- Direct Problem (lat1, lon1, azi, dist -> lat2, lon2) ---")

    t_glib_dir = bench(
        "geographiclib.Direct",
        lambda: GeographiclibGeodesic.WGS84.Direct(*jfk, 51.37, 5_554_000),
    )
    t_rust_dir = bench(
        "geors.direct",
        lambda: direct(*jfk, 51.37, 5_554_000),
    )

    print(f"  geographiclib.Direct:     {t_glib_dir:8.2f} µs")
    print(f"  geors.direct:             {t_rust_dir:8.2f} µs")
    print(f"  Speedup:                  {t_glib_dir / t_rust_dir:8.1f}x")

    # --- Batch geodesic ---
    for n in [1_000, 10_000, 100_000, 1_000_000]:
        print(f"\n--- Batch Geodesic Distance (N={n:,}) ---")
        rng = np.random.default_rng(42)
        lat1 = rng.uniform(-90, 90, n)
        lon1 = rng.uniform(-180, 180, n)
        lat2 = rng.uniform(-90, 90, n)
        lon2 = rng.uniform(-180, 180, n)

        n_iter = max(1, 1000 // (n // 1000))

        # geopy (scalar loop)
        def geopy_batch():
            return [geopy_geodesic((lat1[i], lon1[i]), (lat2[i], lon2[i])).meters for i in range(min(n, 1000))]

        if n <= 10_000:
            t_geopy_batch = bench("geopy batch", geopy_batch, n_iter=max(1, 100 // (n // 1000)))
            t_geopy_batch *= n / min(n, 1000)  # extrapolate
        else:
            t_geopy_batch = None

        t_rust_batch = bench(
            "geors batch",
            lambda: geodesic_distance_batch(lat1, lon1, lat2, lon2),
            n_iter=n_iter,
        )

        throughput = n / (t_rust_batch / 1e6)  # points/sec

        if t_geopy_batch:
            print(f"  geopy (scalar loop):      {t_geopy_batch / 1000:8.2f} ms")
        print(f"  geors (Rust+rayon):       {t_rust_batch / 1000:8.2f} ms")
        print(f"  Throughput:               {throughput / 1e6:8.2f} M pts/sec")
        if t_geopy_batch:
            print(f"  Speedup:                  {t_geopy_batch / t_rust_batch:8.1f}x")

    print("\n" + "=" * 72)
    print("Done.")


if __name__ == "__main__":
    main()
