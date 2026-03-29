"""
geors.distance — drop-in replacement for geopy.distance.

Provides the same API as geopy.distance with Rust-accelerated computation.
"""

from geors._geors import distance as _dist

_geodesic_distance = _dist.geodesic_distance
_geodesic_destination = _dist.geodesic_destination
_geodesic_inverse = _dist.geodesic_inverse
_great_circle_distance = _dist.great_circle_distance
_great_circle_destination = _dist.great_circle_destination
geodesic_distance_batch = _dist.geodesic_distance_batch
great_circle_distance_batch = _dist.great_circle_distance_batch


class Distance:
    """Base distance result, providing unit conversions."""

    def __init__(self, meters: float):
        self._meters = meters

    @property
    def meters(self) -> float:
        return self._meters

    @property
    def m(self) -> float:
        return self._meters

    @property
    def kilometers(self) -> float:
        return self._meters / 1000.0

    @property
    def km(self) -> float:
        return self.kilometers

    @property
    def miles(self) -> float:
        return self._meters / 1609.344

    @property
    def mi(self) -> float:
        return self.miles

    @property
    def feet(self) -> float:
        return self._meters / 0.3048

    @property
    def ft(self) -> float:
        return self.feet

    @property
    def nautical(self) -> float:
        return self._meters / 1852.0

    @property
    def nm(self) -> float:
        return self.nautical

    def __float__(self) -> float:
        return self.km

    def __repr__(self) -> str:
        return f"Distance({self.km:.6f})"

    def __str__(self) -> str:
        return f"{self.km:.6f} km"

    def __eq__(self, other) -> bool:
        if isinstance(other, Distance):
            return self._meters == other._meters
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, Distance):
            return self._meters < other._meters
        return NotImplemented

    def __le__(self, other) -> bool:
        if isinstance(other, Distance):
            return self._meters <= other._meters
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, Distance):
            return self._meters > other._meters
        return NotImplemented

    def __ge__(self, other) -> bool:
        if isinstance(other, Distance):
            return self._meters >= other._meters
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, Distance):
            return Distance(self._meters + other._meters)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Distance):
            return Distance(self._meters - other._meters)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Distance(self._meters * other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)


def _parse_point(point):
    """Parse a point from various formats (matching geopy conventions)."""
    if isinstance(point, (list, tuple)):
        if len(point) >= 2:
            return float(point[0]), float(point[1])
        raise ValueError(f"Point must have at least 2 elements, got {len(point)}")
    if hasattr(point, "latitude") and hasattr(point, "longitude"):
        return float(point.latitude), float(point.longitude)
    raise TypeError(f"Cannot parse point from {type(point)}")


class geodesic(Distance):
    """
    Geodesic (ellipsoidal) distance using Karney's algorithm.

    Drop-in replacement for geopy.distance.geodesic.

    Usage:
        >>> geodesic((40.7128, -74.0060), (51.5074, -0.1278)).km
        5570.248...
    """

    def __new__(cls, point_a=None, point_b=None, **kwargs):
        if point_a is not None and point_b is not None:
            lat1, lon1 = _parse_point(point_a)
            lat2, lon2 = _parse_point(point_b)
            meters = _geodesic_distance(lat1, lon1, lat2, lon2)
            instance = super().__new__(cls)
            instance._meters = meters
            instance._lat1 = lat1
            instance._lon1 = lon1
            instance._lat2 = lat2
            instance._lon2 = lon2
            return instance
        instance = super().__new__(cls)
        instance._meters = 0.0
        return instance

    def __init__(self, point_a=None, point_b=None, **kwargs):
        pass

    def destination(self, point, bearing, distance=None):
        """Calculate destination point given start, bearing, and distance."""
        lat1, lon1 = _parse_point(point)
        if isinstance(distance, Distance):
            dist_m = distance.meters
        elif distance is not None:
            dist_m = float(distance) * 1000.0
        else:
            dist_m = 0.0
        return _geodesic_destination(lat1, lon1, bearing, dist_m)


class great_circle(Distance):
    """
    Great-circle (Haversine) distance on a sphere.

    Drop-in replacement for geopy.distance.great_circle.
    """

    def __new__(cls, point_a=None, point_b=None, **kwargs):
        if point_a is not None and point_b is not None:
            lat1, lon1 = _parse_point(point_a)
            lat2, lon2 = _parse_point(point_b)
            meters = _great_circle_distance(lat1, lon1, lat2, lon2)
            instance = super().__new__(cls)
            instance._meters = meters
            instance._lat1 = lat1
            instance._lon1 = lon1
            instance._lat2 = lat2
            instance._lon2 = lon2
            return instance
        instance = super().__new__(cls)
        instance._meters = 0.0
        return instance

    def __init__(self, point_a=None, point_b=None, **kwargs):
        pass

    def destination(self, point, bearing, distance=None):
        """Calculate destination on great circle."""
        lat1, lon1 = _parse_point(point)
        if isinstance(distance, Distance):
            dist_m = distance.meters
        elif distance is not None:
            dist_m = float(distance) * 1000.0
        else:
            dist_m = 0.0
        return _great_circle_destination(lat1, lon1, bearing, dist_m)


# Default distance is geodesic (same as geopy)
distance = geodesic
