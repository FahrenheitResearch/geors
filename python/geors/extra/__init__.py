"""
geors.extra — forwards to geopy.extra (rate_limiter, etc.).
"""


def __getattr__(name):
    """Lazy-forward to geopy.extra."""
    try:
        import geopy.extra as _extra
        return getattr(_extra, name)
    except ImportError:
        raise ImportError(
            f"geors.extra requires geopy to be installed. "
            f"Install it with: pip install geopy"
        ) from None
    except AttributeError:
        raise AttributeError(
            f"module 'geors.extra' has no attribute '{name}'"
        ) from None
