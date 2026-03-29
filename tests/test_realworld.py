"""
Real-world workflow tests using actual data.

These tests run identical workflows through geopy and geors on real datasets,
comparing every output. If geors is truly a drop-in replacement, every result
must match.

Run: pytest tests/test_realworld.py -v
"""

import pytest
import numpy as np
import json
import urllib.request

# Both libraries under test
import geopy.distance as gd
import geors.distance as rd


# ============================================================
# Real datasets
# ============================================================

# 50 busiest US airports (IATA, lat, lon)
US_AIRPORTS = [
    ("ATL", 33.6407, -84.4277), ("DFW", 32.8998, -97.0403),
    ("DEN", 39.8561, -104.6737), ("ORD", 41.9742, -87.9073),
    ("LAX", 33.9425, -118.4081), ("CLT", 35.2140, -80.9431),
    ("LAS", 36.0840, -115.1537), ("PHX", 33.4373, -112.0078),
    ("MCO", 28.4312, -81.3081), ("SEA", 47.4502, -122.3088),
    ("MIA", 25.7959, -80.2870), ("IAH", 29.9902, -95.3368),
    ("JFK", 40.6413, -73.7781), ("EWR", 40.6895, -74.1745),
    ("SFO", 37.6213, -122.3790), ("MSP", 44.8848, -93.2223),
    ("BOS", 42.3656, -71.0096), ("DTW", 42.2124, -83.3534),
    ("FLL", 26.0742, -80.1506), ("PHL", 39.8744, -75.2424),
    ("BWI", 39.1774, -76.6684), ("SLC", 40.7884, -111.9778),
    ("DCA", 38.8512, -77.0402), ("SAN", 32.7338, -117.1933),
    ("IAD", 38.9531, -77.4565), ("MDW", 41.7868, -87.7522),
    ("TPA", 27.9756, -82.5333), ("HNL", 21.3187, -157.9224),
    ("PDX", 45.5898, -122.5951), ("STL", 38.7487, -90.3700),
    ("BNA", 36.1263, -86.6774), ("AUS", 30.1975, -97.6664),
    ("RDU", 35.8801, -78.7880), ("DAL", 32.8471, -96.8518),
    ("HOU", 29.6454, -95.2789), ("MSY", 29.9934, -90.2580),
    ("SJC", 37.3626, -121.9291), ("OAK", 37.7213, -122.2208),
    ("SMF", 38.6954, -121.5908), ("RSW", 26.5362, -81.7552),
    ("IND", 39.7173, -86.2944), ("PIT", 40.4915, -80.2329),
    ("CVG", 39.0488, -84.6678), ("CMH", 39.9981, -82.8919),
    ("MCI", 39.2976, -94.7139), ("SAT", 29.5337, -98.4698),
    ("CLE", 41.4117, -81.8498), ("OGG", 20.8986, -156.4305),
    ("ABQ", 35.0402, -106.6090), ("MKE", 42.9472, -87.8966),
]

# Global cities (for long-haul routes)
WORLD_CITIES = [
    ("London", 51.5074, -0.1278), ("Tokyo", 35.6762, 139.6503),
    ("Sydney", -33.8688, 151.2093), ("Dubai", 25.2048, 55.2708),
    ("Sao Paulo", -23.5505, -46.6333), ("Mumbai", 19.0760, 72.8777),
    ("Singapore", 1.3521, 103.8198), ("Beijing", 39.9042, 116.4074),
    ("Moscow", 55.7558, 37.6173), ("Cairo", 30.0444, 31.2357),
    ("Nairobi", -1.2921, 36.8219), ("Buenos Aires", -34.6037, -58.3816),
    ("Cape Town", -33.9249, 18.4241), ("Reykjavik", 64.1466, -21.9426),
    ("Auckland", -36.8485, 174.7633), ("Mexico City", 19.4326, -99.1332),
    ("Bangkok", 13.7563, 100.5018), ("Istanbul", 41.0082, 28.9784),
    ("Lima", -12.0464, -77.0428), ("Lagos", 6.5244, 3.3792),
]

# NEXRAD radar sites (real locations)
NEXRAD_SITES = [
    ("KTLX", 35.3331, -97.2778),  # Oklahoma City
    ("KOUN", 35.2456, -97.4717),  # Norman (research)
    ("KVNX", 36.7406, -98.1278),  # Vance AFB
    ("KINX", 36.1750, -95.5647),  # Tulsa
    ("KFDR", 34.3622, -98.9764),  # Altus AFB
    ("KAMA", 35.2331, -101.7092), # Amarillo
    ("KLBB", 33.6536, -101.8142), # Lubbock
    ("KFWS", 32.5731, -97.3031),  # Dallas/Ft Worth
    ("KSRX", 35.2906, -94.3622),  # Ft Smith
    ("KICT", 37.6547, -97.4431),  # Wichita
]

# Historical tornado tracks (start/end points from real events)
TORNADO_TRACKS = [
    # Moore, OK 2013-05-20 EF5
    {"start": (35.306, -97.611), "end": (35.363, -97.335),
     "name": "Moore 2013 EF5"},
    # Joplin, MO 2011-05-22 EF5
    {"start": (37.052, -94.563), "end": (37.068, -94.348),
     "name": "Joplin 2011 EF5"},
    # Tuscaloosa-Birmingham 2011-04-27 EF4
    {"start": (33.101, -87.599), "end": (33.555, -86.851),
     "name": "Tuscaloosa 2011 EF4"},
    # El Reno 2013-05-31 EF5
    {"start": (35.521, -98.072), "end": (35.540, -97.950),
     "name": "El Reno 2013 EF5"},
    # Greensburg, KS 2007-05-04 EF5
    {"start": (37.557, -99.355), "end": (37.648, -99.201),
     "name": "Greensburg 2007 EF5"},
]


# ============================================================
# 1. Airport distance matrix (all-pairs, 50 airports)
# ============================================================

class TestAirportDistanceMatrix:
    """Compute 1225 unique distances between 50 US airports."""

    def test_all_pairs_match(self):
        n = len(US_AIRPORTS)
        max_err = 0.0
        count = 0

        for i in range(n):
            for j in range(i + 1, n):
                a = (US_AIRPORTS[i][1], US_AIRPORTS[i][2])
                b = (US_AIRPORTS[j][1], US_AIRPORTS[j][2])

                gd_km = gd.geodesic(a, b).km
                rd_km = rd.geodesic(a, b).km
                err = abs(gd_km - rd_km)
                max_err = max(max_err, err)
                count += 1

                assert err < 1e-6, (
                    f"{US_AIRPORTS[i][0]}->{US_AIRPORTS[j][0]}: "
                    f"geopy={gd_km:.6f}, geors={rd_km:.6f}, err={err:.2e}"
                )

        assert count == 1225  # C(50,2)
        print(f"\n  1225 airport pairs: max error = {max_err:.2e} km")

    def test_great_circle_all_pairs(self):
        n = len(US_AIRPORTS)
        max_err = 0.0

        for i in range(n):
            for j in range(i + 1, n):
                a = (US_AIRPORTS[i][1], US_AIRPORTS[i][2])
                b = (US_AIRPORTS[j][1], US_AIRPORTS[j][2])

                gd_km = gd.great_circle(a, b).km
                rd_km = rd.great_circle(a, b).km
                err = abs(gd_km - rd_km)
                max_err = max(max_err, err)

        print(f"\n  1225 great-circle pairs: max error = {max_err:.2e} km")
        assert max_err < 1e-3  # great circle uses slightly different constants


# ============================================================
# 2. Global long-haul routes
# ============================================================

class TestGlobalRoutes:
    """Test intercontinental routes including tricky cases."""

    def test_all_pairs(self):
        n = len(WORLD_CITIES)
        max_err = 0.0

        for i in range(n):
            for j in range(i + 1, n):
                a = (WORLD_CITIES[i][1], WORLD_CITIES[i][2])
                b = (WORLD_CITIES[j][1], WORLD_CITIES[j][2])

                gd_d = gd.geodesic(a, b)
                rd_d = rd.geodesic(a, b)

                # Check all unit conversions match
                assert abs(gd_d.km - rd_d.km) < 1e-6
                assert abs(gd_d.miles - rd_d.miles) < 1e-6
                assert abs(gd_d.meters - rd_d.meters) < 1e-3
                assert abs(gd_d.nautical - rd_d.nautical) < 1e-6

                max_err = max(max_err, abs(gd_d.km - rd_d.km))

        print(f"\n  190 global route pairs: max error = {max_err:.2e} km")

    def test_longest_routes(self):
        """Verify the longest possible routes (near-antipodal)."""
        near_antipodal = [
            ((0, 0), (0, 179.99)),
            ((89.99, 0), (-89.99, 180)),
            ((-45, -170), (45, 10)),
        ]
        for a, b in near_antipodal:
            gd_km = gd.geodesic(a, b).km
            rd_km = rd.geodesic(a, b).km
            assert abs(gd_km - rd_km) < 1e-6, (
                f"Near-antipodal {a}->{b}: diff={abs(gd_km-rd_km):.2e} km"
            )


# ============================================================
# 3. NEXRAD radar coverage analysis
# ============================================================

class TestRadarCoverage:
    """Real radar site proximity and coverage calculations."""

    def test_radar_to_radar_distances(self):
        """All inter-radar distances match."""
        n = len(NEXRAD_SITES)
        for i in range(n):
            for j in range(i + 1, n):
                a = (NEXRAD_SITES[i][1], NEXRAD_SITES[i][2])
                b = (NEXRAD_SITES[j][1], NEXRAD_SITES[j][2])
                gd_km = gd.geodesic(a, b).km
                rd_km = rd.geodesic(a, b).km
                assert abs(gd_km - rd_km) < 1e-6

    def test_coverage_rings(self):
        """Compute 230km range ring points for each radar (destination)."""
        range_km = 230
        bearings = list(range(0, 360, 10))  # every 10 degrees

        for name, lat, lon in NEXRAD_SITES:
            for bearing in bearings:
                gd_pt = gd.geodesic(kilometers=range_km).destination(
                    (lat, lon), bearing=bearing
                )
                rd_pt = rd.geodesic(kilometers=range_km).destination(
                    (lat, lon), bearing=bearing
                )
                assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-8, (
                    f"{name} bearing {bearing}: lat diff"
                )
                assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-8, (
                    f"{name} bearing {bearing}: lon diff"
                )

    def test_point_in_coverage(self):
        """Which radars cover Moore, OK? Must agree."""
        moore = (35.3387, -97.4864)
        max_range_km = 230

        gd_covering = []
        rd_covering = []
        for name, lat, lon in NEXRAD_SITES:
            if gd.geodesic(moore, (lat, lon)).km <= max_range_km:
                gd_covering.append(name)
            if rd.geodesic(moore, (lat, lon)).km <= max_range_km:
                rd_covering.append(name)

        assert gd_covering == rd_covering, (
            f"Coverage mismatch: geopy={gd_covering}, geors={rd_covering}"
        )


# ============================================================
# 4. Tornado track analysis
# ============================================================

class TestTornadoTracks:
    """Real tornado track measurements."""

    def test_track_lengths(self):
        """Path length of each tornado must match."""
        for t in TORNADO_TRACKS:
            gd_km = gd.geodesic(t["start"], t["end"]).km
            rd_km = rd.geodesic(t["start"], t["end"]).km
            assert abs(gd_km - rd_km) < 1e-6, (
                f"{t['name']}: geopy={gd_km:.4f}, geors={rd_km:.4f}"
            )

    def test_track_bearings(self):
        """Storm motion direction (azimuth) must match."""
        from geors._geors import geodesic as _geo

        for t in TORNADO_TRACKS:
            from geographiclib.geodesic import Geodesic
            gd_r = Geodesic.WGS84.Inverse(
                t["start"][0], t["start"][1],
                t["end"][0], t["end"][1]
            )
            rd_r = _geo.inverse(
                t["start"][0], t["start"][1],
                t["end"][0], t["end"][1]
            )
            assert abs(gd_r["azi1"] - rd_r["azi1"]) < 1e-6, (
                f"{t['name']}: azimuth mismatch"
            )

    def test_interpolate_track_points(self):
        """Generate evenly spaced points along a tornado track."""
        t = TORNADO_TRACKS[0]  # Moore 2013
        track_km = gd.geodesic(t["start"], t["end"]).km
        n_points = 20
        spacing_km = track_km / n_points

        # Get initial bearing
        from geographiclib.geodesic import Geodesic
        r = Geodesic.WGS84.Inverse(
            t["start"][0], t["start"][1],
            t["end"][0], t["end"][1]
        )
        bearing = r["azi1"]

        for i in range(n_points + 1):
            dist_km = i * spacing_km
            gd_pt = gd.geodesic(kilometers=dist_km).destination(
                t["start"], bearing=bearing
            )
            rd_pt = rd.geodesic(kilometers=dist_km).destination(
                t["start"], bearing=bearing
            )
            assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-8, (
                f"Track point {i}: lat mismatch"
            )
            assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-8, (
                f"Track point {i}: lon mismatch"
            )


# ============================================================
# 5. Batch processing (the killer feature)
# ============================================================

class TestBatchProcessing:
    """Verify batch operations match scalar on real data patterns."""

    def test_airport_batch(self):
        """Batch all airport-to-JFK distances."""
        jfk = US_AIRPORTS[12]  # JFK
        lats = np.array([a[1] for a in US_AIRPORTS])
        lons = np.array([a[2] for a in US_AIRPORTS])
        jfk_lats = np.full(len(US_AIRPORTS), jfk[1])
        jfk_lons = np.full(len(US_AIRPORTS), jfk[2])

        batch_m = rd.geodesic_distance_batch(jfk_lats, jfk_lons, lats, lons)

        for i, (code, lat, lon) in enumerate(US_AIRPORTS):
            scalar_km = rd.geodesic((jfk[1], jfk[2]), (lat, lon)).km
            batch_km = batch_m[i] / 1000.0
            assert abs(scalar_km - batch_km) < 1e-6, (
                f"JFK->{code}: scalar={scalar_km:.4f}, batch={batch_km:.4f}"
            )

    def test_random_global_batch(self):
        """100K random global point pairs — batch vs geopy spot check."""
        rng = np.random.default_rng(42)
        n = 100_000
        lat1 = rng.uniform(-90, 90, n)
        lon1 = rng.uniform(-180, 180, n)
        lat2 = rng.uniform(-90, 90, n)
        lon2 = rng.uniform(-180, 180, n)

        batch_m = rd.geodesic_distance_batch(lat1, lon1, lat2, lon2)

        # Spot-check 50 against geopy
        indices = rng.choice(n, 50, replace=False)
        max_err = 0.0
        for i in indices:
            gd_m = gd.geodesic((lat1[i], lon1[i]), (lat2[i], lon2[i])).meters
            err = abs(batch_m[i] - gd_m)
            max_err = max(max_err, err)
            assert err < 1e-3, (
                f"Index {i}: geopy={gd_m:.6f}m, geors_batch={batch_m[i]:.6f}m"
            )

        print(f"\n  100K batch vs geopy spot check: max error = {max_err:.2e} m")


# ============================================================
# 6. Multi-leg route planning
# ============================================================

class TestRoutePlanning:
    """Multi-stop route distance calculations."""

    def test_cross_country_route(self):
        """NYC -> Chicago -> Denver -> LA -> Seattle total distance."""
        route = [
            (40.7128, -74.0060),   # NYC
            (41.8781, -87.6298),   # Chicago
            (39.7392, -104.9903),  # Denver
            (34.0522, -118.2437),  # LA
            (47.6062, -122.3321),  # Seattle
        ]
        gd_total = gd.geodesic(*route)
        rd_total = rd.geodesic(*route)
        assert abs(gd_total.km - rd_total.km) < 1e-6
        assert abs(gd_total.miles - rd_total.miles) < 1e-6

    def test_around_the_world(self):
        """Full circumnavigation route through world cities."""
        route = [
            (51.5074, -0.1278),   # London
            (25.2048, 55.2708),   # Dubai
            (19.0760, 72.8777),   # Mumbai
            (1.3521, 103.8198),   # Singapore
            (35.6762, 139.6503),  # Tokyo
            (21.3187, -157.9224), # Honolulu
            (37.6213, -122.3790), # SFO
            (40.7128, -74.0060),  # NYC
            (51.5074, -0.1278),   # London (return)
        ]
        gd_total = gd.geodesic(*route)
        rd_total = rd.geodesic(*route)
        assert abs(gd_total.km - rd_total.km) < 1e-5
        print(f"\n  Around the world: {rd_total.km:.1f} km "
              f"({rd_total.miles:.1f} miles)")

    def test_destination_chain(self):
        """Chain of destinations: go 100km north, then 100km east, etc."""
        start = (35.0, -97.0)  # central Oklahoma

        gd_pos = start
        rd_pos = start

        legs = [(0, 100), (90, 100), (180, 100), (270, 100)]  # N, E, S, W
        for bearing, dist_km in legs:
            gd_pt = gd.geodesic(kilometers=dist_km).destination(gd_pos, bearing)
            rd_pt = rd.geodesic(kilometers=dist_km).destination(rd_pos, bearing)

            assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-8
            assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-8

            gd_pos = (gd_pt.latitude, gd_pt.longitude)
            rd_pos = (rd_pt.latitude, rd_pt.longitude)

        # After N-E-S-W 100km each, should be close to start (not exact due to curvature)
        final_dist = rd.geodesic(start, rd_pos).km
        assert final_dist < 2.0  # within ~2km due to convergence of meridians
