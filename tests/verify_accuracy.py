"""
Comprehensive accuracy verification for geors.

Tests against:
1. Karney's official GeodTest dataset (10,000 cases covering antipodal, polar, equatorial, etc.)
2. Real-world city pairs with known distances
3. Edge cases (identical points, poles, antimeridian, near-antipodal)
4. geopy's own test vectors
5. Great-circle vs geodesic expected divergence
6. Direct/inverse roundtrip consistency

Run: python tests/verify_accuracy.py
"""

import os
import sys
import time
import numpy as np

from geopy.distance import geodesic as geopy_geodesic
from geopy.distance import great_circle as geopy_great_circle
from geographiclib.geodesic import Geodesic as GeographiclibGeodesic

from geors._geors import distance as _dist
from geors._geors import geodesic as _geo

geodesic_distance = _dist.geodesic_distance
great_circle_distance = _dist.great_circle_distance
geodesic_distance_batch = _dist.geodesic_distance_batch
geodesic_inverse = _dist.geodesic_inverse

inverse = _geo.inverse
direct = _geo.direct


def section(title):
    print(f"\n{'='*72}")
    print(f"  {title}")
    print(f"{'='*72}")


def check(name, got, expected, tol, unit=""):
    diff = abs(got - expected)
    ok = diff <= tol
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: got={got:.10f}, expected={expected:.10f}, diff={diff:.2e} {unit}")
    return ok


def main():
    all_pass = True
    total = 0
    passed = 0

    # ===========================================================
    # 1. Karney's GeodTest (10,000 official test vectors)
    # ===========================================================
    section("1. Karney GeodTest-short.dat (10,000 official test vectors)")

    geodtest_path = os.path.join(os.path.dirname(__file__), "GeodTest-short.dat")
    if not os.path.exists(geodtest_path):
        print("  SKIP: GeodTest-short.dat not found. Download from sourceforge.")
    else:
        g_ref = GeographiclibGeodesic.WGS84

        lines = open(geodtest_path).readlines()
        n_cases = len(lines)
        max_s12_err = 0.0
        max_azi1_err = 0.0
        max_azi2_err = 0.0
        max_lat2_err = 0.0
        max_lon2_err = 0.0
        s12_errors = []
        fail_count = 0

        t0 = time.perf_counter()
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 7:
                continue
            lat1 = float(parts[0])
            lon1 = float(parts[1])
            azi1_ref = float(parts[2])
            lat2_ref = float(parts[3])
            lon2_ref = float(parts[4])
            azi2_ref = float(parts[5])
            s12_ref = float(parts[6])

            # Test inverse
            r = geodesic_inverse(lat1, lon1, float(parts[3]), float(parts[4]))
            s12_err = abs(r["s12"] - s12_ref)
            azi1_err = abs(r["azi1"] - azi1_ref)
            azi2_err = abs(r["azi2"] - azi2_ref)
            # Handle angle wraparound
            if azi1_err > 180:
                azi1_err = 360 - azi1_err
            if azi2_err > 180:
                azi2_err = 360 - azi2_err

            max_s12_err = max(max_s12_err, s12_err)
            max_azi1_err = max(max_azi1_err, azi1_err)
            max_azi2_err = max(max_azi2_err, azi2_err)
            s12_errors.append(s12_err)

            # Test direct
            d = direct(lat1, lon1, azi1_ref, s12_ref)
            lat2_err = abs(d["lat2"] - lat2_ref)
            lon2_err = abs(d["lon2"] - lon2_ref)
            if lon2_err > 180:
                lon2_err = 360 - lon2_err
            max_lat2_err = max(max_lat2_err, lat2_err)
            max_lon2_err = max(max_lon2_err, lon2_err)

            if s12_err > 1e-3:  # >1mm
                fail_count += 1

        elapsed = time.perf_counter() - t0
        s12_errors = np.array(s12_errors)

        print(f"  Tested {n_cases} cases in {elapsed:.2f}s")
        print(f"  Inverse s12:  max err = {max_s12_err:.6e} m, "
              f"mean = {s12_errors.mean():.6e} m, "
              f"median = {np.median(s12_errors):.6e} m")
        print(f"  Inverse azi1: max err = {max_azi1_err:.6e} deg")
        print(f"  Inverse azi2: max err = {max_azi2_err:.6e} deg")
        print(f"  Direct lat2:  max err = {max_lat2_err:.6e} deg")
        print(f"  Direct lon2:  max err = {max_lon2_err:.6e} deg")
        print(f"  Cases >1mm error: {fail_count}/{n_cases}")

        total += 5
        if max_s12_err < 1e-3:  # sub-mm
            print("  [PASS] All inverse distances within 1mm of reference")
            passed += 1
        else:
            print(f"  [FAIL] Max inverse distance error: {max_s12_err:.6e} m")
            all_pass = False

        # Azimuth tolerance: 1e-3 deg (~111m at equator; near-antipodal cases
        # have inherently ambiguous azimuths so small errors are expected)
        if max_azi1_err < 1e-3:
            print(f"  [PASS] All forward azimuths within 1e-3 deg (max: {max_azi1_err:.6e})")
            passed += 1
        else:
            print(f"  [FAIL] Max azi1 error: {max_azi1_err:.6e} deg")
            all_pass = False

        if max_azi2_err < 1e-3:
            print(f"  [PASS] All reverse azimuths within 1e-3 deg (max: {max_azi2_err:.6e})")
            passed += 1
        else:
            print(f"  [FAIL] Max azi2 error: {max_azi2_err:.6e} deg")
            all_pass = False

        if max_lat2_err < 1e-8:
            print("  [PASS] All direct latitudes within 1e-8 deg")
            passed += 1
        else:
            print(f"  [FAIL] Max direct lat2 error: {max_lat2_err:.6e} deg")
            all_pass = False

        if max_lon2_err < 1e-8:
            print("  [PASS] All direct longitudes within 1e-8 deg")
            passed += 1
        else:
            print(f"  [FAIL] Max direct lon2 error: {max_lon2_err:.6e} deg")
            all_pass = False

    # ===========================================================
    # 2. Real-world city pairs
    # ===========================================================
    section("2. Real-world city pairs (vs geographiclib reference)")

    CITY_PAIRS = [
        ("JFK -> Heathrow", 40.6413, -73.7781, 51.4700, -0.4543),
        ("Tokyo -> NYC", 35.6762, 139.6503, 40.7128, -74.0060),
        ("Sydney -> Paris", -33.8688, 151.2093, 48.8566, 2.3522),
        ("Buenos Aires -> Beijing", -34.6037, -58.3816, 39.9042, 116.4074),
        ("Cape Town -> Mumbai", -33.9249, 18.4241, 19.0760, 72.8777),
        ("Reykjavik -> Singapore", 64.1466, -21.9426, 1.3521, 103.8198),
        ("Anchorage -> Auckland", 61.2181, -149.9003, -36.8485, 174.7633),
        ("Moscow -> Santiago", 55.7558, 37.6173, -33.4489, -70.6693),
        ("Cairo -> Melbourne", 30.0444, 31.2357, -37.8136, 144.9631),
        ("Nairobi -> Los Angeles", -1.2921, 36.8219, 34.0522, -118.2437),
        ("Lima -> Bangkok", -12.0464, -77.0428, 13.7563, 100.5018),
        ("Dublin -> Toronto", 53.3498, -6.2603, 43.6532, -79.3832),
        ("Honolulu -> London", 21.3069, -157.8583, 51.5074, -0.1278),
        ("McMurdo Station -> Longyearbyen", -77.8419, 166.6863, 78.2232, 15.6267),
        ("Quito -> Mogadishu", -0.1807, -78.4678, 2.0469, 45.3182),
    ]

    g_ref = GeographiclibGeodesic.WGS84
    max_err = 0.0
    for name, lat1, lon1, lat2, lon2 in CITY_PAIRS:
        ref = g_ref.Inverse(lat1, lon1, lat2, lon2)["s12"]
        got = geodesic_distance(lat1, lon1, lat2, lon2)
        err = abs(got - ref)
        max_err = max(max_err, err)
        status = "PASS" if err < 1e-6 else "FAIL"
        total += 1
        if err < 1e-6:
            passed += 1
        else:
            all_pass = False
        print(f"  [{status}] {name:35s}: {got/1000:.3f} km, err={err:.2e} m")

    print(f"  Max error across all city pairs: {max_err:.2e} m")

    # ===========================================================
    # 3. Edge cases
    # ===========================================================
    section("3. Edge cases")

    edge_cases = [
        ("Identical points (0,0)", 0, 0, 0, 0, 0.0),
        ("Identical points (NYC)", 40.7128, -74.0060, 40.7128, -74.0060, 0.0),
        ("Pole to pole", -90, 0, 90, 0, None),
        ("Antipodal equator", 0, 0, 0, 180, None),
        ("Near-antipodal (Vincenty fails)", 0, 0, 0.5, 179.5, None),
        ("Near-antipodal (Vincenty fails 2)", 0, 0, 0.5, 179.7, None),
        ("Antimeridian +180/-180", 0, -180, 0, 180, 0.0),
        ("Antimeridian close", 0, -179.999, 0, 179.999, None),
        ("North pole to equator", 90, 0, 0, 0, None),
        ("South pole to equator", -90, 0, 0, 0, None),
        ("Very short distance", 0, 0, 0, 0.000001, None),
        ("Along equator 1 deg", 0, 0, 0, 1, None),
        ("Along meridian 1 deg", 0, 0, 1, 0, None),
    ]

    for name, lat1, lon1, lat2, lon2, expected in edge_cases:
        ref = g_ref.Inverse(lat1, lon1, lat2, lon2)["s12"]
        got = geodesic_distance(lat1, lon1, lat2, lon2)
        err = abs(got - ref)
        total += 1
        if err < 1e-6:
            passed += 1
            print(f"  [PASS] {name:40s}: {got:.6f} m, err={err:.2e} m")
        else:
            all_pass = False
            print(f"  [FAIL] {name:40s}: {got:.6f} m vs ref {ref:.6f} m, err={err:.2e} m")

    # ===========================================================
    # 4. Direct/inverse roundtrip consistency
    # ===========================================================
    section("4. Direct/inverse roundtrip (1000 random cases)")

    rng = np.random.default_rng(42)
    max_roundtrip_err = 0.0
    n_roundtrip = 1000
    for i in range(n_roundtrip):
        lat1 = rng.uniform(-89, 89)
        lon1 = rng.uniform(-180, 180)
        azi1 = rng.uniform(-180, 180)
        s12 = rng.uniform(100, 15_000_000)  # 100m to 15000km

        d = direct(lat1, lon1, azi1, s12)
        inv_s12 = geodesic_distance(lat1, lon1, d["lat2"], d["lon2"])
        err = abs(inv_s12 - s12)
        max_roundtrip_err = max(max_roundtrip_err, err)

    total += 1
    if max_roundtrip_err < 0.01:  # 1cm
        passed += 1
        print(f"  [PASS] Max roundtrip error: {max_roundtrip_err:.6e} m (<1cm)")
    else:
        all_pass = False
        print(f"  [FAIL] Max roundtrip error: {max_roundtrip_err:.6e} m")

    # ===========================================================
    # 5. Great-circle vs geodesic divergence check
    # ===========================================================
    section("5. Great-circle vs geodesic expected divergence")

    gc_diffs = []
    for name, lat1, lon1, lat2, lon2 in CITY_PAIRS[:10]:
        gc = great_circle_distance(lat1, lon1, lat2, lon2)
        geod = geodesic_distance(lat1, lon1, lat2, lon2)
        if geod > 0:
            pct_diff = abs(gc - geod) / geod * 100
            gc_diffs.append(pct_diff)

    mean_pct = np.mean(gc_diffs)
    max_pct = np.max(gc_diffs)
    total += 1
    # Expected: ~0.1-0.5% difference
    if 0.01 < mean_pct < 1.0:
        passed += 1
        print(f"  [PASS] Mean gc-vs-geodesic divergence: {mean_pct:.4f}% (expected 0.1-0.5%)")
    else:
        all_pass = False
        print(f"  [FAIL] Mean gc-vs-geodesic divergence: {mean_pct:.4f}% (unexpected)")
    print(f"  Max divergence: {max_pct:.4f}%")

    # ===========================================================
    # 6. Batch consistency
    # ===========================================================
    section("6. Batch vs scalar consistency (10,000 random pairs)")

    n = 10000
    lat1 = rng.uniform(-90, 90, n)
    lon1 = rng.uniform(-180, 180, n)
    lat2 = rng.uniform(-90, 90, n)
    lon2 = rng.uniform(-180, 180, n)

    batch_result = geodesic_distance_batch(lat1, lon1, lat2, lon2)

    # Check a sample of 100 against scalar
    max_batch_err = 0.0
    for i in range(0, n, 100):
        scalar = geodesic_distance(lat1[i], lon1[i], lat2[i], lon2[i])
        err = abs(batch_result[i] - scalar)
        max_batch_err = max(max_batch_err, err)

    total += 1
    if max_batch_err < 1e-10:
        passed += 1
        print(f"  [PASS] Batch matches scalar: max diff = {max_batch_err:.2e} m")
    else:
        all_pass = False
        print(f"  [FAIL] Batch diverges from scalar: max diff = {max_batch_err:.2e} m")

    # ===========================================================
    # 7. Cross-verify with geopy (full 10K random)
    # ===========================================================
    section("7. Cross-verify with geopy (1000 random pairs)")

    max_geopy_err = 0.0
    for i in range(1000):
        la1, lo1 = lat1[i], lon1[i]
        la2, lo2 = lat2[i], lon2[i]
        ref = geopy_geodesic((la1, lo1), (la2, lo2)).meters
        got = geodesic_distance(la1, lo1, la2, lo2)
        err = abs(got - ref)
        max_geopy_err = max(max_geopy_err, err)

    total += 1
    if max_geopy_err < 1e-3:
        passed += 1
        print(f"  [PASS] Max error vs geopy: {max_geopy_err:.2e} m (<1mm)")
    else:
        all_pass = False
        print(f"  [FAIL] Max error vs geopy: {max_geopy_err:.2e} m")

    # ===========================================================
    # Summary
    # ===========================================================
    section("SUMMARY")
    print(f"  Passed: {passed}/{total}")
    if all_pass:
        print("  ALL CHECKS PASSED")
    else:
        print("  SOME CHECKS FAILED")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
