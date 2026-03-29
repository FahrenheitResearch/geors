"""
geors — Rust-powered drop-in replacement for geopy.

Usage:
    from geors.distance import geodesic, great_circle, distance
    from geors.geocoders import Nominatim  # forwards to geopy
"""

__version__ = "0.1.0"

from geors.distance import geodesic, great_circle, distance
