"""
geors.geocoders — forwards to geopy.geocoders.

Geocoding is I/O-bound (HTTP requests), so we forward to the original
geopy implementation. This keeps geors as a drop-in replacement.
"""


def __getattr__(name):
    """Lazy-forward all geocoder imports to geopy."""
    try:
        import geopy.geocoders as _geocoders
        return getattr(_geocoders, name)
    except ImportError:
        raise ImportError(
            f"geors.geocoders requires geopy to be installed for geocoder access. "
            f"Install it with: pip install geopy"
        ) from None
    except AttributeError:
        raise AttributeError(
            f"module 'geors.geocoders' has no attribute '{name}'"
        ) from None
